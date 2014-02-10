from flask import Flask, jsonify, request
from crossdomain import crossdomain
from datetime import datetime

import MySQLdb as db

app = Flask(__name__)
app.debug = True

@app.route('/user/<token>/challenge', methods=['GET', 'OPTIONS'])
@crossdomain(origin='*', methods=['GET', 'OPTIONS'], headers=['X-Requested-With', 'Content-Type', 'Origin'])
def sendChallenge(token):
  conn = db.connect(
    host = "mysql-user.stanford.edu",
    user = "gsislhero",
    passwd = "eepulood",
    db = "g_sisl_hero")
  cursor = conn.cursor()
  cursor.execute("""
  SELECT
   HCD.SequencePattern,
   HCD.ShowLetters,
   HCD.LetterColor,
   HCD.LetterSize,
   HCD.NumKeys,
   HCD.Keys,
   HCD.BubbleColor,
   HCD.ConfigDataID
  FROM        g_sisl_hero.Hero_User HU
  INNER JOIN  g_sisl_hero.Hero_Config HC
  ON          (
                HC.ConfigID = HU.ConfigID AND 
                HC.ConfigDataNumber = HU.ConfigDataNumber
              )
  INNER JOIN  g_sisl_hero.Hero_ConfigData HCD
  ON          (
                HCD.ConfigDataID = HC.ConfigDataID
              )
  WHERE       HU.Token = %s
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

    return jsonify(
      patterntime=patterntime,
      patternkeys=patternkeys,
      showLetters=row[1],
      letterColor=row[2],
      letterSize=row[3],
      numkeys=row[4],
      keys=row[5].split(' '),
      bubbleColor=row[6].split(' '),
      expNumber=row[7]
    )

@app.route('/user/<token>/response/<int:expnumber>', methods=['POST', 'OPTIONS'])
@crossdomain(origin='*', methods=['POST', 'OPTIONS'], headers=['X-Requested-With', 'Content-Type', 'Origin'])
def getResponse(token, expnumber):
  expNumber = request.json['expNumber']
  batchId = request.json['batchId']
  responses = request.json['responses']
  end = request.json['end']

  # Update experice number if all sequence has been played
  if end:
    pass
    data = int(expNumber) + 1
    conn = db.connect(
      host = "mysql-user.stanford.edu",
      user = "gsislhero",
      passwd = "eepulood",
      db = "g_sisl_hero")
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE g_sisl_hero.Hero_User SET ConfigDataNumber=%s
    """, [data])
    cursor.close()
    conn.close()

  # Store responses sent
  if len(responses):
    ft = '%Y-%m-%d %H:%M:%S.%f'

    data = [
      (
        token, 
        expNumber, 
        datetime.fromtimestamp(int(x['responseKeyDate'])/1000).strftime(ft),
        batchId,
        datetime.now().strftime(ft),
        x['key'],
        1 if x['hit'] else 0,
        x['offset'],
        x['closestKey'],
        x['queuePosition'],
      )
      for x in responses
    ]

    print len(data)

    conn = db.connect(
      host = "mysql-user.stanford.edu",
      user = "gsislhero",
      passwd = "eepulood",
      db = "g_sisl_hero")
    cursor = conn.cursor()
    cursor.executemany("""
    INSERT INTO g_sisl_hero.Hero_ResponseKey (
      Token,
      ExpNumber,
      ResponseKeyDatetime,
      BatchID,
      BatchDatetime,
      KeyID,
      HitFlag,
      Offset,
      ClosestKeyID,
      QueuePosition
    )
    VALUES
      (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, data)
    cursor.close()
    conn.close()

  return 'OK'

 
if __name__ == '__main__':
  app.run()
