#!/usr/bin/env python3

import json
import socket

class Client:

	def __init__(self, host="localhost", port=31337):
		try:
			self.sock = socket.socket()
			self.sock.connect((host,port))
		except Exception as error:
			print(error)


	def guess(self, word):
		guess = {
					"guess": word,
					"hard": True
				}
		self.sock.send(bytes(json.dumps(guess), "utf-8"))


	def response(self):
		return json.loads(self.sock.recv(256))


	def display(self, data):
		print(data)


	def run(self):
		print("Press enter with an empty prompt to terminate")

		while True:
			client_guess = input("Send to server: ")
			if client_guess == '':
				break

			self.guess(client_guess)
			self.display(self.response())

		self.sock.close()
		print("Terminating...")


if __name__ == "__main__":
	Client().run()