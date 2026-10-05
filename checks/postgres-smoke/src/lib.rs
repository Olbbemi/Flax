//! Independent consumer checks; this crate is not a Rosemary storage library.

#[cfg(test)]
mod tests {
    use parking_lot::RwLock;
    use rustls_pki_types::{pem::PemObject, CertificateDer};
    use sha2::{Digest, Sha256};

    #[test]
    fn pem_ca_bytes_parse_in_memory_and_malformed_certificates_are_rejected() {
        let certificates: Vec<_> =
            CertificateDer::pem_slice_iter(include_bytes!("../fixtures/ca.pem"))
                .collect::<Result<_, _>>()
                .unwrap();
        assert_eq!(certificates.len(), 1);
        assert!(!certificates[0].is_empty());
        let malformed = b"-----BEGIN CERTIFICATE-----\n!invalid!\n-----END CERTIFICATE-----\n";
        assert!(CertificateDer::from_pem_slice(malformed).is_err());
    }

    #[test]
    fn sha256_matches_the_known_abc_digest() {
        let digest: String = Sha256::digest(b"abc")
            .iter()
            .map(|byte| format!("{byte:02x}"))
            .collect();
        assert_eq!(
            digest,
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }

    #[test]
    fn rwlock_shares_reads_excludes_writes_and_reacquires_after_guard_drop() {
        let lock = RwLock::new(7);
        let first = lock.read();
        let second = lock.try_read().expect("reads may share the lock");
        assert_eq!((*first, *second), (7, 7));
        assert!(lock.try_write().is_none());
        drop(first);
        drop(second);
        let mut writer = lock.try_write().expect("read guards released");
        *writer = 9;
        assert!(lock.try_read().is_none());
        assert!(lock.try_write().is_none());
        drop(writer);
        assert_eq!(*lock.try_read().expect("write guard released"), 9);
    }
}
