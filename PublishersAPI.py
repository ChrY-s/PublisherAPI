from bson import ObjectId
from pymongo import AsyncMongoClient

import tornado
from tornado.web import Application, RequestHandler

import nest_asyncio
import asyncio
import json

nest_asyncio.apply()

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

        # Controllo se l'utente ha inserito dei filtri nella QS
        # - name
        # - country
        try:
            name_filter = self.get_argument("name")
        except:
            name_filter = None

        try:
            country_filter = self.get_argument("country")
        except:
            country_filter = None

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

        # Applico gli eventuali filtri
        country_filtered = []

        if country_filter:
            # unfiltered publisher
            for upb in response:
                if upb['country'] == country_filter:
                    country_filtered.append(upb)
        else:
            country_filtered = response

        name_filtered = []

        if name_filter:
            # unfiltered publisher
            for upb in country_filtered:
                if upb["name"] == name_filter:
                    name_filtered.append(upb)
        else:
            name_filtered = country_filtered

        self.write({"ok": name_filtered})
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

        # Converto l'id del publisher solo per l'invio in json
        data["_id"] = str(data["_id"])

        self.set_status(201)
        self.write({"ok": data})

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

        await publishers_collection.update_one({"_id": ObjectId(publisher_id)}, {"$set" : { "name" : new_name,
                                                                                                        "founded_year" : new_year,
                                                                                                        "country" : new_country } })

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
    # Mostro uno o piu libri
    async def get(self, publisher_id, book_id = None):
        self.set_header("Content-Type", "application/json")

        # Controllo se l'utente ha inserito dei filtri nella QS
        # - title
        # - author
        # - genre
        try:
            title_filter = self.get_argument("title")
        except:
            title_filter = None

        try:
            author_filter = self.get_argument("author")
        except:
            author_filter = None

        try:
            genre_filter = self.get_argument("genre")
        except:
            genre_filter = None

        # Se non indico un libro preciso restituisce tutti i libri
        if not book_id:
            # lista con tutti i libri
            books = []

            # Dati di tutti i libri della casa editrice
            bk_data = books_collection.find({"publisher_id": publisher_id})

            # Inserisco tutti i libri nella lista che invierò alla pagina html
            async for bk in bk_data:
                # Converto l'id BSON in STR
                bk["_id"] = str(bk["_id"])

                books.append(bk)

            # Risposta da inviare
            response = books

        # Mostro il libro desiderato
        else:
            # Trovo il libro a cui corrisponde l'id
            bk = await books_collection.find_one({"publisher_id": publisher_id,
                                                  "_id" : ObjectId(book_id)})

            # Non ho trovato un indice corrispondente
            if not bk:
                self.write({"error": "resource not found"})
                self.set_status(404)
                return

            # Converto l'id BSON in STR
            bk["_id"] = str(bk["_id"])

            # Risposta da inviare
            response = bk

        title_filtered = []
        # Applico gli eventuali filtri
        if title_filter:
            # unfiltered book
            for ub in response:
                if ub["title"] == title_filter:
                    title_filtered.append(ub)
        else:
            title_filtered = response

        author_filtered = []
        if author_filter:
            # unfiltered book
            for ub in title_filtered:
                if ub["author"] == author_filter:
                    author_filtered.append(ub)
        else:
            author_filtered = title_filtered

        genre_filtered = []
        if genre_filter:
            # unfiltered book
            for ub in author_filtered:
                if ub["genre"] == genre_filter:
                    genre_filtered.append(ub)
        else:
            genre_filtered = author_filtered

        self.write({"ok": genre_filtered})
        self.set_status(200)

    # Aggiungo un libro
    async def post(self, publisher_id, book_id):
        self.set_header("Content-Type", "application/json")

        # Controllo se ho inviato dei dati
        try:
            data = tornado.escape.json_decode(self.request.body)
        except:
            self.set_status(400)
            self.write({"error": "Insert data"})
            return

        # Inserisco il libro nel DB
        await books_collection.insert_one(data)

        # Converto l'id del libri solo per l'invio in json
        data["_id"] = str(data["_id"])

        self.set_status(201)
        self.write({"ok": data})

    # Aggiorno un libro
    async def put(self, publisher_id, book_id):
        self.set_header("Content-Type", "application/json")

        # Controllo se ho inviato dei dati
        try:
            data = tornado.escape.json_decode(self.request.body)
        except:
            self.set_status(400)
            self.write({"error": "Insert data"})
            return

        # Prendo l'id del libro
        new_title = data["title"]
        new_author = data["author"]
        new_genre = data["genre"]
        new_year = data["year"]

        # Controllo se esiste
        try:
            await books_collection.find_one({"_id": ObjectId(book_id)})
        except:
            self.set_status(400)
            self.write({"error": "ID not existent"})
            return

        await books_collection.update_one({"_id": ObjectId(book_id)}, {"$set": {"title": new_title,
                                                                                          "author": new_author,
                                                                                          "genre": new_genre,
                                                                                          "year": new_year}})

        self.set_status(202)
        self.write({"ok": json.dumps(data)})

    # Elimino un libro
    async def delete(self, publisher_id, book_id):
        self.set_header("Content-Type", "application/json")

        # Controllo se esiste l'id del libro
        try:
            await books_collection.find_one({"_id": ObjectId(book_id)})
        except:
            self.set_status(400)
            self.write({"error": "ID not existent"})
            return

        # Rimuovo il libro
        await books_collection.delete_one({"_id": ObjectId(book_id)})

        self.set_status(202)
        self.write({"ok": "publisher deleted"})


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
