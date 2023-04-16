import hashlib
import json
from time import time
from uuid import uuid4
from textwrap import dedent
from flask import Flask, jsonify, request


class Blockzain(object):
    def __init__(self):
        self.zain = []
        self.transactions = []

        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.zain) + 1,
            'timestamp': time(),
            'transactions': self.transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.zain[-1])
        }

        self.transactions = []
        self.zain.append(block)

        return block

    def new_transaction(self, sender, recipient, amount):
        self.transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.zain[-1]

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

    def pow(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof


app = Flask(__name__)

identifier = str(uuid4()).replace('-', '')
blockzain = Blockzain()


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockzain.last_block
    last_proof = last_block['proof']
    proof = blockzain.pow(last_proof)

    blockzain.new_transaction(
        sender='0',
        recipient=identifier,
        amount=1
    )

    previous_hash = blockzain.hash(last_block)
    block = blockzain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Created",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }

    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    vals = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in vals for k in required):
        return 'Missing Values', 400

    index = blockzain.new_transaction(vals['sender'], vals['recipient'], vals['amount'])
    response = {'message': f'Transaction will be added to block {index}'}

    return jsonify(response), 201


@app.route('/zain', methods=['GET'])
def full_zain():
    response = {
        'zain': blockzain.zain,
        'length': len(blockzain.zain)
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
