from bson import ObjectId
from pymongo import AsyncMongoClient
import asyncio
from tornado.web import Application, RequestHandler

import json

# DB Mongo con cui posso interagire
client = AsyncMongoClient("localhost", 27017)

# Imposto riferimenti a db e collezioni
db = client["publisher_db"]
publishers_collection = db["publishers"]
books_collection = db["books"]

# Publisher handler
class PublisherHandler(RequestHandler):
    async def get(self, id = None):
        self.set_header("Content-Type", "application/json")

        # Se non indico un publisher preciso restituisce tutte le case editrici
        if not id:
            # lista con tutti i publisher
            publishers = []

            # Dati di tutti i publishers
            pb_data = publishers_collection.find()

            # Inserisco tutti i publisher nella lista che invierò alla pagina html
            async for pb in pb_data:
                # Converto l'id BSON in STR
                pb["_id"] = str(pb["_id"])

                publishers.append(pb)

            # Risposta da inviare
            response = publishers

        # Mostro la casa editrice desiderata
        else:
            # Trovo il publisher a cui corrisponde l'id
            pb = await publishers_collection.find_one({"_id": ObjectId(id)})

            # Non ho trovato un indice corrispondente
            if not pb:
                self.write({"error": "resource not found"})
                self.set_status(404)
                return

            # Converto l'id BSON in STR
            pb["_id"] = str(pb["_id"])

            # Risposta da inviare
            response = pb

        self.write({"ok": response})
        self.set_status(200)

    def post(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

# Book handler
class BookHandler(RequestHandler):
    def get(self):
        pass

    def post(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass


def make_app():
    return Application([
        (r'/publishers', PublisherHandler),
        (r'/publishers/([ 0-9 | a-z | A-Z ]+)', PublisherHandler),
        (r'/publishers/([ 0-9 | a-z | A-Z ]+)/books', BookHandler),
        (r'/publishers/([ 0-9 | a-z | A-Z ]+)/books/([ 0-9 | a-z | A-Z ]+)', BookHandler)
    ])

async def main(stop):
    app = make_app()
    app.listen(8888)
    print("Server listening at http://localhost:8888/publishers ...")

    await stop.wait()
    print("Server closed")

if __name__ == '__main__':
    stop_event = asyncio.Event()

    try:
        asyncio.run(main(stop_event))
    except KeyboardInterrupt:
        stop_event.set()
