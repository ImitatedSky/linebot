import os

import firebase_admin
from firebase_admin import credentials, firestore

# 組成服務帳戶金鑰 JSON
service_account_info = {
    "type": os.environ.get("SERVICE_ACCOUNT_TYPE"),
    "project_id": os.environ.get("SERVICE_ACCOUNT_PROJECT_ID"),
    "private_key_id": os.environ.get("SERVICE_ACCOUNT_PRIVATE_KEY_ID"),
    "private_key": os.environ.get("SERVICE_ACCOUNT_PRIVATE_KEY").replace(
        "\\n", "\n"
    ),
    "client_email": os.environ.get("SERVICE_ACCOUNT_CLIENT_EMAIL"),
    "client_id": os.environ.get("SERVICE_ACCOUNT_CLIENT_ID"),
    "auth_uri": os.environ.get("SERVICE_ACCOUNT_AUTH_URI"),
    "token_uri": os.environ.get("SERVICE_ACCOUNT_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.environ.get(
        "SERVICE_ACCOUNT_AUTH_PROVIDER_X509_CERT_URL"
    ),
    "client_x509_cert_url": os.environ.get(
        "SERVICE_ACCOUNT_CLIENT_X509_CERT_URL"
    ),
    "universe_domain": os.environ.get("SERVICE_ACCOUNT_UNIVERSE_DOMAIN"),
}

# 初始化 Firebase Admin SDK
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred)

# 初始化 Firestore 客戶端
db = firestore.client()


class FirestoreDB:
    def __init__(self, collection_name):
        self.collection_name = collection_name
        self.collection_ref = db.collection(collection_name)

    def write_document(self, doc_id, data):
        """
        create
        return DocumentReference
        """
        doc_ref = self.collection_ref.document(doc_id)
        doc_ref.set(data, merge=True)
        # print(
        #     f"Document {doc_id} successfully written in {self.collection_name} collection!"
        # )
        return doc_ref

    def read_document(self, doc_id):
        """
        read/search
        return dict
        """
        doc_ref = self.collection_ref.document(doc_id)
        doc = doc_ref.get()
        # type(doc) => <class 'google.cloud.firestore_v1.document.DocumentSnapshot'>

        # if doc.exists:
        #     print(f"{doc.id} => {doc.to_dict()}")
        # else:
        #     print(
        #         f"Document {doc_id} does not exist in {self.collection_name} collection."
        #     )
        return doc.to_dict()

    def read_collection(self):
        """
        read all document in collection
        return dict
        """
        docs = self.collection_ref.stream()
        result = {}
        for doc in docs:
            result[doc.id] = doc.to_dict()
        return result

    def update_document(self, doc_id, updates):
        """
        update
        return DocumentReference
        """
        doc_ref = self.collection_ref.document(doc_id)
        doc_ref.update(updates)
        # print(
        #     f"Document {doc_id} successfully updated in {self.collection_name} collection!"
        # )
        return doc_ref

    def delete_document(self, doc_id):
        """
        delete
        return DocumentReference
        """
        doc_ref = self.collection_ref.document(doc_id)
        doc_ref.delete()
        # print(
        #     f"Document {doc_id} successfully deleted from {self.collection_name} collection!"
        # )
        return doc_ref

    def search_document(self, doc_id):
        """
        search
        return dict
        """
        doc_ref = self.collection_ref.document(doc_id)
        doc = doc_ref.get()
        # if doc.exists:
        #     print(f"{doc.id} => {doc.to_dict()}")
        # else:
        #     print(
        #         f"Document {doc_id} does not exist in {self.collection_name} collection."
        #     )
        return doc.to_dict()

    def search_by_name(self, name):
        """
        search
        return
        """
        results = self.collection_ref.stream()
        for doc in results:
            data = doc.to_dict()
            if name in data:
                print(f"{doc.id} => {data[name]}")
        return results
