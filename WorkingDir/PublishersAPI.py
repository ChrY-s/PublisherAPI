from bson import ObjectId
from pymongo import AsyncMongoClient

import tornado
from tornado.web import Application, RequestHandler

import asyncio
import json

# DB Mongo con cui posso interagire
client = AsyncMongoClient("localhost", 27017)

# Imposto riferimenti a db e collezioni
db = client["publisher_db"]
publishers_collection = db["publishers"]
books_collection = db["books"]

# Publisher handler
class PublisherHandler(RequestHandler):
    # Ricerca una casa editrice
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

    # Aggiunge una casa editrice
    async def post(self):
        self.set_header("Content-Type", "application/json")

        # Controllo se ho inviato dei dati
        try:
            data = tornado.escape.json_decode(self.request.body)
        except:
            self.set_status(400)
            self.write({"error": "Insert data"})
            return

        # Inserisco il publisher nel DB
        await publishers_collection.insert_one(data)

        self.set_status(201)
        self.write({"ok": json.dumps(data)})

    # Modifico un publisher
    async def put(self, id):
        self.set_header("Content-Type", "application/json")

        # Controllo se ho inviato dei dati
        try:
            data = tornado.escape.json_decode(self.request.body)
        except:
            self.set_status(400)
            self.write({"error": "Insert data"})
            return

        # Prendo l'id del publisher
        publisher_id = id
        new_name = data["name"]
        new_year = data["founded_year"]
        new_country = data["country"]

        # Controllo se esiste
        try:
            await publishers_collection.find_one({"_id": ObjectId(publisher_id)})
        except:
            self.set_status(400)
            self.write({"error": "ID not existent"})
            return

        await publishers_collection.update_one({"_id": ObjectId(publisher_id)}, { "name" : new_name,
                                                                                            "founded_year" : new_year,
                                                                                            "country" : new_country })

        self.set_status(202)
        self.write({"ok": json.dumps(data)})

    # Rimuovo il publisher
    async def delete(self, id):
        self.set_header("Content-Type", "application/json")

        # Controllo se esiste l'id del publisher
        try:
            await publishers_collection.find_one({"_id": ObjectId(id)})
        except:
            self.set_status(400)
            self.write({"error": "ID not existent"})
            return

        # Rimuovo il publisher
        await publishers_collection.delete_one({"_id": ObjectId(id)})

        self.set_status(202)
        self.write({"ok": "publisher deleted"})

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
