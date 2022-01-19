#!/usr/bin/env python3

import argparse
import json
import jsonschema
import logging, logging.config
import random
import socketserver
import threading

schema = {
	"type": "object",
	"properties": {
		"guess": {"type": "string"},
		"hard": {"type": "boolean"}
	},
	"required": ["guess", "hard"]
}

class Wordle(socketserver.StreamRequestHandler):

	def handle(self):

		# Validate guess JSON provided by client.
		def validate_client_guess(msg):
			raw_guess = json.loads(msg)
			jsonschema.validate(instance=raw_guess, schema=schema)
			
			guess = raw_guess["guess"].lower()
			if len(guess) != 5 or guess not in self.server.wordlist:
				print(len(guess))
				print(guess not in self.server.wordlist)
				raise ValueError("Guess not in dictionary.")

			return guess


		# Send message to client
		def respond(resp):
			self.request.send(bytes(json.dumps(resp), "utf-8"))


		# Get logger and log new connection
		self.log = logging.getLogger('wordle')
		self.log.info("Connection from %s:%s opened", self.client_address[0], self.client_address[1])

		while True:

			# Choose new word.
			word = server.wordlist[random.randint(0, len(server.wordlist)-1)]

			# Respond to guesses (maximum of 6 properly formatted guesses)
			guess_counter = 0
			while guess_counter < 6:

				# Receive guess from client and process
				msg = self.request.recv(256)
				
				# Assume disconnect from client.
				if msg == b'':
					break

				# Check that client response is valid.
				try:
					guess = validate_client_guess(msg)
					self.log.info(msg.decode("utf-8"))

				# Issue with actual format of JSON, could not be parsed.
				except json.decoder.JSONDecodeError as error:
					self.log.error("Improperly formatted JSON: %s", error)
					respond({
								"error": "Improperly formatted JSON",
								"schema": schema
							})
					continue

				# JSON is valid but does not match required schema.
				except jsonschema.exceptions.ValidationError as error:
					self.log.error("Given JSON does not match schema: %s", error)
					respond({
								"error": "Given JSON does not match schema",
								"schema": schema
							})
					continue

				# User guess is not 5 letters long or is not in the wordlist.
				except ValueError as error:
					self.log.error(error)
					respond({
								"error": "Guess must be 5 letters long and in wordlist"
							})
					continue

				# Generate hint and send to client
				hint = ""
				for i, letter in enumerate(guess):
					result = 0

					if letter in word:
						result = 1
					if letter == word[i]:
						result = 2

					hint += str(result)

				respond({
							"hint": hint,
							"guess_count": guess_counter + 1,
							"word": word 
					   })
				guess_counter += 1
			

			# If loop did not exit normally, assume user disconnected and terminate
			else:
				continue
			break

		# Log disconnect
		self.log.info("Connection from %s:%s closed", self.client_address[0], self.client_address[1])


# Execute
if __name__ == "__main__":

	# Parse arguments
	parser = argparse.ArgumentParser(description="Command line Wordle server")
	parser.add_argument("host", help="domain or IPv4 address for TCP server")
	parser.add_argument("port", help="port for TCP server", type=int)
	parser.add_argument("wordlist", help="path to wordlist file composed of newline delimited, 5 letter words")
	args = parser.parse_args()

	# Instantiate server
	with socketserver.ThreadingTCPServer((args.host, args.port), Wordle) as server:

		# Prepare logger
		logging.config.fileConfig('logging.conf')
		logging.getLogger('worlde').info("Bound to %s:%s", args.host, args.port)

		# Retrieve wordlist
		with open(args.wordlist, "r") as wl:
			server.wordlist = [line.rstrip() for line in wl]

		# Start server
		server.serve_forever()