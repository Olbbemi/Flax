pub mod generated {
    tonic::include_proto!("flax.check");
}

#[cfg(test)]
mod tests {
    use super::generated::{
        echo_client::EchoClient,
        echo_server::{Echo, EchoServer},
        EchoReply, EchoRequest,
    };
    use std::time::Duration;
    use tokio::{net::TcpListener, sync::oneshot, time::timeout};
    use tokio_stream::wrappers::TcpListenerStream;
    use tonic::{transport::Server, Code, Request, Response, Status};

    #[derive(Default)]
    struct EchoService;

    #[tonic::async_trait]
    impl Echo for EchoService {
        async fn send(&self, request: Request<EchoRequest>) -> Result<Response<EchoReply>, Status> {
            let request = request.into_inner();
            if request.text.is_empty() {
                return Err(Status::invalid_argument("text is required"));
            }
            Ok(Response::new(EchoReply {
                text: request.text,
                payload: request.payload,
            }))
        }
    }

    #[tokio::test]
    async fn generated_client_and_server_exchange_messages_and_status() {
        timeout(Duration::from_secs(15), async {
            let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
            let address = listener.local_addr().unwrap();
            let (stop, stopped) = oneshot::channel();
            let server = tokio::spawn(async move {
                Server::builder()
                    .add_service(EchoServer::new(EchoService))
                    .serve_with_incoming_shutdown(TcpListenerStream::new(listener), async {
                        let _ = stopped.await;
                    })
                    .await
                    .unwrap();
            });
            let mut client = EchoClient::connect(format!("http://{address}"))
                .await
                .unwrap();
            let reply = client
                .send(EchoRequest {
                    text: "일정 확인".into(),
                    payload: vec![0, 1, 127, 128, 255],
                })
                .await
                .unwrap()
                .into_inner();
            assert_eq!(reply.text, "일정 확인");
            assert_eq!(reply.payload, [0, 1, 127, 128, 255]);
            let error = client.send(EchoRequest::default()).await.unwrap_err();
            assert_eq!(error.code(), Code::InvalidArgument);
            drop(client);
            stop.send(()).unwrap();
            server.await.unwrap();
        })
        .await
        .expect("gRPC check timed out");
    }
}
