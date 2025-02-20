import grpc

# Import the generated classes
import ts.dexhand.v1.dexhand_service_pb2_grpc as dexhand_pb2
import ts.dexhand.v1.dexhand_control_service_pb2_grpc as dexhand_control_pb2


def run():
    # Create a gRPC channel to the server
    channel = grpc.insecure_channel("localhost:50051")
    # Create a stub (client)
    stub = dexhand_pb2.DexHandServiceStub(channel)
    # Prepare the request (adjust fields as required)
    request = dexhand_pb2.TestRequest()
    # Call the RPC method
    response = stub.TestMethod(request)
    print("Response from server:", response)


if __name__ == "__main__":
    run()
