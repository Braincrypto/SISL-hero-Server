from flask import Flask, jsonify
import MySQLdb as db

app = Flask(__name__)

@app.route('/')
def hello_world():
  return 'Hello World!'

@app.route('/test')
def json():
  return jsonify(
    username='Hello',
    email='Coucou',
    id='myid'
  )

@app.route('/test2')
def login():
  conn = db.connect(
    host = "mysql-user.stanford.edu",
    user = "gsislhero",
    passwd = "eepulood",
    db = "g_sisl_hero")
  cursor = conn.cursor()
  cursor.execute("SELECT VERSION()")
  row = cursor.fetchone()
  cursor.close()
  conn.close()

  return "server version:" + str(row[0])

@app.route('/user/<token>/challenge')
def challengeInfo(token):
  conn = db.connect(
    host = "mysql-user.stanford.edu",
    user = "gsislhero",
    passwd = "eepulood",
    db = "g_sisl_hero")
  cursor = conn.cursor()
  cursor.execute("""
  SELECT 
   AP.SequencePattern,
   AP.ShowLetters,
   AP.LetterColor,
   AP.LetterSize,
   AP.NumKeys,
   AP.Keys,
   AP.BubbleColor
  FROM        g_sisl_hero.hero_AuthParam AP
  INNER JOIN  g_sisl_hero.hero_AuthUser AU
  ON          (AP.SequenceID = AU.SequenceID)
  WHERE       AU.Token = %s
  """, [token])
  row = cursor.fetchone()
  cursor.close()
  conn.close()

  if row is None:
    return "Nothing"

  else:
    pattern = row[0].split('\t')
    patterntime = pattern[::2]
    patternkeys = [int(i)-1 for i in pattern[1::2]]

    response = jsonify(
    patterntime=patterntime,
    patternkeys=patternkeys,
    showLetters=row[1],
    letterColor=row[2],
    letterSize=row[3],
    numkeys=row[4],
    keys=row[5].split(' '),
    bubbleColor=row[6].split(' '),
    )

    response.headers['Access-Control-Allow-Origin'] = "*" 

    return response

if __name__ == '__main__':
  app.run()
