use std::{env, error::Error, fs, net::IpAddr, sync::Arc, time::Duration};

use deadpool_postgres::{
    Manager, ManagerConfig, Pool, PoolError, RecyclingMethod, Runtime, TimeoutType,
};
use rustls::{crypto::CryptoProvider, ClientConfig, RootCertStore, SupportedProtocolVersion};
use rustls_pki_types::{pem::PemObject, CertificateDer};
use tokio::{task::JoinHandle, time::timeout};
use tokio_postgres::{config::SslMode, error::SqlState, Client, Config, NoTls};
use tokio_postgres_rustls::MakeRustlsConnect;

const TLS12: &[&SupportedProtocolVersion] = &[&rustls::version::TLS12];
const TLS13: &[&SupportedProtocolVersion] = &[&rustls::version::TLS13];
const BOTH: &[&SupportedProtocolVersion] = &[&rustls::version::TLS12, &rustls::version::TLS13];
type DriverTask = JoinHandle<Result<(), tokio_postgres::Error>>;

fn input(name: &str) -> String {
    env::var(name).unwrap_or_else(|_| panic!("missing {name}; run checks/postgres-smoke/run.py"))
}

fn config(port: &str, mode: SslMode) -> Config {
    let mut config = Config::new();
    config
        .host(&input("FLAX_PG_HOST"))
        .hostaddr(input("FLAX_PG_HOSTADDR").parse::<IpAddr>().unwrap())
        .port(input(port).parse().unwrap())
        .user(&input("FLAX_PG_USER"))
        .dbname(&input("FLAX_PG_DATABASE"))
        .password(input("FLAX_PG_PASSWORD"))
        .application_name("flax-postgres-smoke")
        .connect_timeout(Duration::from_secs(5))
        .ssl_mode(mode);
    config
}

fn connector(
    ca: &str,
    versions: &'static [&'static SupportedProtocolVersion],
) -> MakeRustlsConnect {
    let bytes = fs::read(input(ca)).unwrap();
    let mut roots = RootCertStore::empty();
    let certificates: Vec<_> = CertificateDer::pem_slice_iter(&bytes)
        .collect::<Result<_, _>>()
        .unwrap();
    assert!(
        !certificates.is_empty(),
        "CA must come from supplied PEM bytes"
    );
    for certificate in certificates {
        roots.add(certificate).unwrap();
    }
    let config =
        ClientConfig::builder_with_provider(Arc::new(rustls::crypto::ring::default_provider()))
            .with_protocol_versions(versions)
            .unwrap()
            .with_root_certificates(roots)
            .with_no_client_auth();
    MakeRustlsConnect::new(config)
}

async fn plain(config: &Config) -> Result<(Client, DriverTask), tokio_postgres::Error> {
    let (client, connection) = timeout(Duration::from_secs(5), config.connect(NoTls))
        .await
        .expect("plain connection deadline")?;
    Ok((client, tokio::spawn(connection)))
}

async fn tls(
    config: &Config,
    ca: &str,
    versions: &'static [&'static SupportedProtocolVersion],
) -> Result<(Client, DriverTask), tokio_postgres::Error> {
    let (client, connection) = timeout(
        Duration::from_secs(5),
        config.connect(connector(ca, versions)),
    )
    .await
    .expect("TLS connection deadline")?;
    Ok((client, tokio::spawn(connection)))
}

async fn close(client: Client, task: DriverTask) {
    drop(client);
    timeout(Duration::from_secs(5), task)
        .await
        .expect("driver shutdown deadline")
        .unwrap()
        .unwrap();
}

fn failure_reason(error: &dyn Error) -> String {
    let mut messages = error.to_string();
    let mut source = error.source();
    while let Some(error) = source {
        messages.push_str(&error.to_string());
        source = error.source();
    }
    messages
        .chars()
        .filter(|character| character.is_ascii_alphanumeric())
        .flat_map(char::to_lowercase)
        .collect()
}

fn rejected(result: Result<(Client, DriverTask), tokio_postgres::Error>) -> tokio_postgres::Error {
    match result {
        Err(error) => error,
        Ok((client, task)) => {
            drop(client);
            task.abort();
            panic!("connection unexpectedly succeeded")
        }
    }
}

fn pool(encrypted: bool) -> Pool {
    let config = config(
        "FLAX_PG_PORT",
        if encrypted {
            SslMode::Require
        } else {
            SslMode::Disable
        },
    );
    let options = ManagerConfig {
        recycling_method: RecyclingMethod::Verified,
    };
    let manager = if encrypted {
        Manager::from_config(config, connector("FLAX_PG_CA", BOTH), options)
    } else {
        Manager::from_config(config, NoTls, options)
    };
    Pool::builder(manager)
        .max_size(2)
        .wait_timeout(Some(Duration::from_millis(100)))
        .create_timeout(Some(Duration::from_secs(5)))
        .recycle_timeout(Some(Duration::from_secs(5)))
        .runtime(Runtime::Tokio1)
        .build()
        .unwrap()
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn scram_authenticates_on_and_off_and_rejects_wrong_passwords() {
    let off = config("FLAX_PG_PORT", SslMode::Disable);
    let (client, task) = plain(&off).await.unwrap();
    let row = client
        .query_one("SELECT current_user::text", &[])
        .await
        .unwrap();
    assert_eq!(row.get::<_, String>(0), input("FLAX_PG_USER"));
    close(client, task).await;
    let on = config("FLAX_PG_PORT", SslMode::Require);
    let (client, task) = tls(&on, "FLAX_PG_CA", BOTH).await.unwrap();
    let row = client
        .query_one("SELECT current_user::text", &[])
        .await
        .unwrap();
    assert_eq!(row.get::<_, String>(0), input("FLAX_PG_USER"));
    close(client, task).await;
    let mut wrong_off = off.clone();
    wrong_off.password("intentionally-wrong-flax-test-password");
    let error = rejected(plain(&wrong_off).await);
    assert_eq!(
        error.as_db_error().unwrap().code(),
        &SqlState::INVALID_PASSWORD
    );
    let mut wrong_on = on;
    wrong_on.password("intentionally-wrong-flax-test-password");
    let error = rejected(tls(&wrong_on, "FLAX_PG_CA", BOTH).await);
    assert_eq!(
        error.as_db_error().unwrap().code(),
        &SqlState::INVALID_PASSWORD
    );
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn tls12_and_tls13_verify_supplied_ca_and_leave_global_provider_unset() {
    assert!(CryptoProvider::get_default().is_none());
    for (versions, expected) in [(TLS12, "TLSv1.2"), (TLS13, "TLSv1.3")] {
        let (client, task) = tls(
            &config("FLAX_PG_PORT", SslMode::Require),
            "FLAX_PG_CA",
            versions,
        )
        .await
        .unwrap();
        let row = client
            .query_one(
                "SELECT ssl, version FROM pg_stat_ssl WHERE pid = pg_backend_pid()",
                &[],
            )
            .await
            .unwrap();
        assert!(row.get::<_, bool>(0));
        assert_eq!(row.get::<_, String>(1), expected);
        close(client, task).await;
    }
    assert!(CryptoProvider::get_default().is_none());
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn wrong_ca_is_rejected_as_an_untrusted_issuer() {
    let config = config("FLAX_PG_PORT", SslMode::Require);
    let (client, task) = tls(&config, "FLAX_PG_CA", BOTH).await.unwrap();
    close(client, task).await;
    let error = rejected(tls(&config, "FLAX_PG_WRONG_CA", BOTH).await);
    assert!(
        failure_reason(&error).contains("unknownissuer"),
        "{error:?}"
    );
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn wrong_target_name_is_rejected_on_the_same_reachable_server() {
    let config = config("FLAX_PG_PORT", SslMode::Require);
    let (client, task) = tls(&config, "FLAX_PG_CA", BOTH).await.unwrap();
    close(client, task).await;
    // Keep hostaddr; only the certificate's target name changes.
    // Config::host appends; construct a single-host negative case explicitly.
    let mut wrong = Config::new();
    wrong
        .host("wrong-name.invalid")
        .hostaddr(input("FLAX_PG_HOSTADDR").parse::<IpAddr>().unwrap())
        .port(input("FLAX_PG_PORT").parse().unwrap())
        .user(&input("FLAX_PG_USER"))
        .dbname(&input("FLAX_PG_DATABASE"))
        .password(input("FLAX_PG_PASSWORD"))
        .ssl_mode(SslMode::Require)
        .connect_timeout(Duration::from_secs(5));
    let error = rejected(tls(&wrong, "FLAX_PG_CA", BOTH).await);
    assert!(
        failure_reason(&error).contains("notvalidforname"),
        "{error:?}"
    );
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn expired_certificate_is_rejected_while_plain_scram_still_works() {
    let off = config("FLAX_PG_EXPIRED_PORT", SslMode::Disable);
    let (client, task) = plain(&off).await.unwrap();
    client.simple_query("SELECT 1").await.unwrap();
    close(client, task).await;
    let error = rejected(
        tls(
            &config("FLAX_PG_EXPIRED_PORT", SslMode::Require),
            "FLAX_PG_CA",
            BOTH,
        )
        .await,
    );
    assert!(failure_reason(&error).contains("expired"), "{error:?}");
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn tls_required_does_not_fall_back_on_a_plain_only_server() {
    let (client, task) = plain(&config("FLAX_PG_PLAIN_PORT", SslMode::Disable))
        .await
        .unwrap();
    client.simple_query("SELECT 1").await.unwrap();
    close(client, task).await;
    let error = rejected(
        tls(
            &config("FLAX_PG_PLAIN_PORT", SslMode::Require),
            "FLAX_PG_CA",
            BOTH,
        )
        .await,
    );
    assert!(
        failure_reason(&error).contains("doesnotsupporttls"),
        "{error:?}"
    );
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn encrypted_and_plain_pools_coexist_and_enforce_size_and_wait_timeout() {
    let on = pool(true);
    let off = pool(false);
    let on_client = on.get().await.unwrap();
    let off_client = off.get().await.unwrap();
    for (client, encrypted) in [(&on_client, true), (&off_client, false)] {
        let row = client
            .query_one(
                "SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()",
                &[],
            )
            .await
            .unwrap();
        assert_eq!(row.get::<_, bool>(0), encrypted);
    }
    let second = on.get().await.unwrap();
    let pid1: i32 = on_client
        .query_one("SELECT pg_backend_pid()", &[])
        .await
        .unwrap()
        .get(0);
    let pid2: i32 = second
        .query_one("SELECT pg_backend_pid()", &[])
        .await
        .unwrap()
        .get(0);
    assert_ne!(pid1, pid2);
    assert_eq!(on.status().size, 2);
    let error = timeout(Duration::from_secs(2), on.get())
        .await
        .unwrap()
        .unwrap_err();
    assert!(matches!(error, PoolError::Timeout(TimeoutType::Wait)));
    drop(second);
    let reacquired = on.get().await.unwrap();
    reacquired.simple_query("SELECT 1").await.unwrap();
    assert_eq!(on.status().size, 2);
    drop(reacquired);
    drop(on_client);
    drop(off_client);
    on.close();
    off.close();
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn commit_rollback_and_sql_error_cleanup_allow_later_queries() {
    let pool = pool(false);
    let mut first = pool.get().await.unwrap();
    let second = pool.get().await.unwrap();
    first
        .batch_execute("CREATE TABLE flax_transactions (id INTEGER PRIMARY KEY)")
        .await
        .unwrap();
    let pid1: i32 = first
        .query_one("SELECT pg_backend_pid()", &[])
        .await
        .unwrap()
        .get(0);
    let pid2: i32 = second
        .query_one("SELECT pg_backend_pid()", &[])
        .await
        .unwrap()
        .get(0);
    assert_ne!(pid1, pid2);
    let transaction = first.transaction().await.unwrap();
    transaction
        .execute("INSERT INTO flax_transactions VALUES (1)", &[])
        .await
        .unwrap();
    transaction.commit().await.unwrap();
    assert_eq!(
        second
            .query_one("SELECT count(*) FROM flax_transactions WHERE id=1", &[])
            .await
            .unwrap()
            .get::<_, i64>(0),
        1
    );
    let transaction = first.transaction().await.unwrap();
    transaction
        .execute("INSERT INTO flax_transactions VALUES (2)", &[])
        .await
        .unwrap();
    transaction.rollback().await.unwrap();
    assert_eq!(
        second
            .query_one("SELECT count(*) FROM flax_transactions WHERE id=2", &[])
            .await
            .unwrap()
            .get::<_, i64>(0),
        0
    );
    let transaction = first.transaction().await.unwrap();
    let error = transaction
        .query_one("SELECT 1 / 0", &[])
        .await
        .unwrap_err();
    assert_eq!(
        error.as_db_error().unwrap().code(),
        &SqlState::DIVISION_BY_ZERO
    );
    transaction.rollback().await.unwrap();
    drop(first);
    let healthy = pool.get().await.unwrap();
    assert_eq!(
        healthy
            .query_one("SELECT 1::integer", &[])
            .await
            .unwrap()
            .get::<_, i32>(0),
        1
    );
    drop(healthy);
    drop(second);
    pool.close();
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn bytea_numeric_decimal_u64_text_and_integer_round_trip() {
    let (client, task) = plain(&config("FLAX_PG_PORT", SslMode::Disable))
        .await
        .unwrap();
    client
        .batch_execute(
            "CREATE TABLE flax_values (id BIGSERIAL PRIMARY KEY, bytes BYTEA NOT NULL, \
         number NUMERIC NOT NULL, text_value TEXT NOT NULL, int_value INTEGER NOT NULL)",
        )
        .await
        .unwrap();
    let bytes = vec![0_u8, 1, 127, 128, 255, 0, 42];
    let text = "Rosemary 저장 검증";
    let integer = i32::MIN;
    let maximum = u64::MAX.to_string();
    for number in [
        "1234567890.123456789012345678901234567890",
        maximum.as_str(),
    ] {
        let row = client
            .query_one(
                "INSERT INTO flax_values (bytes,number,text_value,int_value) \
             VALUES ($1,$2::text::numeric,$3,$4) RETURNING id",
                &[&bytes, &number, &text, &integer],
            )
            .await
            .unwrap();
        let id: i64 = row.get(0);
        let row = client
            .query_one(
                "SELECT bytes, number::text, text_value, int_value FROM flax_values WHERE id=$1",
                &[&id],
            )
            .await
            .unwrap();
        assert_eq!(row.get::<_, Vec<u8>>(0), bytes);
        assert_eq!(row.get::<_, String>(1), number);
        assert_eq!(row.get::<_, String>(2), text);
        assert_eq!(row.get::<_, i32>(3), integer);
    }
    close(client, task).await;
}
