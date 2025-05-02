#!/usr/bin/env python3
import os
import argparse
import grpc
import json
import time
from google.protobuf.empty_pb2 import Empty

# Путь к вашему файлу со схемой
DEFAULT_SCHEMA_FILE = "schema.perm"

def read_schema(file_path):
    """Читает содержимое файла схемы"""
    with open(file_path, 'r') as f:
        return f.read()

def main():
    parser = argparse.ArgumentParser(description='Permify gRPC Client')
    parser.add_argument('--address', default='localhost:9011', help='gRPC address')
    parser.add_argument('--schema', default=DEFAULT_SCHEMA_FILE, help='Path to schema file')
    parser.add_argument('--tenant', default='t1', help='Tenant ID')
    parser.add_argument('--action', choices=['schema', 'relationships', 'check'], 
                        default='schema', help='Action to perform')
    parser.add_argument('--relationships', help='Path to relationships JSON file')
    
    args = parser.parse_args()
    
    # Создаем канал gRPC
    channel = grpc.insecure_channel(args.address)
    
    if args.action == 'schema':
        # Загрузка схемы
        if os.path.exists(args.schema):
            schema_content = read_schema(args.schema)
            print(f"Loaded schema from {args.schema}:")
            print(schema_content)
            print("\nTo import this schema, you need to use the Permify gRPC API client.")
            print("Install the permify-python client from GitHub and use:")
            print(f"from permify.api.v1 import schema_pb2, schema_pb2_grpc")
            print(f"schema_stub = schema_pb2_grpc.SchemaServiceStub(channel)")
            print(f"response = schema_stub.Write(schema_pb2.SchemaWriteRequest(tenant_id='{args.tenant}', schema='{schema_content}'))")
        else:
            print(f"Schema file {args.schema} not found!")
    
    elif args.action == 'relationships':
        # Загружаем отношения
        if not args.relationships:
            print("Please specify --relationships file path")
            return
        
        if os.path.exists(args.relationships):
            with open(args.relationships, 'r') as f:
                relationships = json.load(f)
            print(f"Loaded relationships from {args.relationships}:")
            print(json.dumps(relationships, indent=2))
            print("\nTo import these relationships, you need to use the Permify gRPC API client.")
            print("Install the permify-python client from GitHub and use:")
            print(f"from permify.api.v1 import data_pb2, data_pb2_grpc")
            print(f"data_stub = data_pb2_grpc.DataServiceStub(channel)")
            print(f"response = data_stub.Write(data_pb2.DataWriteRequest(tenant_id='{args.tenant}', tuples=[...]))")
        else:
            print(f"Relationships file {args.relationships} not found!")
    
    elif args.action == 'check':
        print("Check action selected")
        print("To check permissions, you need to use the Permify gRPC API client.")
        print("Install the permify-python client from GitHub and use:")
        print(f"from permify.api.v1 import permission_pb2, permission_pb2_grpc")
        print(f"perm_stub = permission_pb2_grpc.PermissionServiceStub(channel)")
        print(f"response = perm_stub.Check(permission_pb2.PermissionCheckRequest(tenant_id='{args.tenant}', entity=..., permission='...', subject=...))")

if __name__ == "__main__":
    main() 