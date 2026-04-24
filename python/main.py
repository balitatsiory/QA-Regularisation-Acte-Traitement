import helper as h
from flask import Flask, jsonify, request
import traceback

app = Flask(__name__)


@app.route('/api', methods=['POST'])
def read_item():
   idaffaire = request.form['idaffaire']
   print(f"Received idaffaire: {idaffaire}")
   if not idaffaire:
      return jsonify({"error": "idaffaire est requis"}), 400
   try:
      traitement = h.Traitement()
      traitementIdAffaire=traitement.traitementIdAffaire(idaffaire)
      return jsonify({"status": "ok", "idaffaire": idaffaire,"traitementIdAffaire":traitementIdAffaire}), 200
   except Exception as e:
      traceback.print_exc()
      return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
   print("Starting Flask API on port 5000...")
   app.run(port=5000)