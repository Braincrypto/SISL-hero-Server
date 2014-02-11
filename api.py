from flask import Flask, jsonify, request
from crossdomain import crossdomain
import time

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
   HU.ConfigDataNumber,
   HCD.SequencePattern,
   HCD.ShowLetters,
   HCD.LetterColor,
   HCD.LetterSize,
   HCD.NumKeys,
   HCD.Keys,
   HCD.BubbleColor,
   HCD.BatchSize,
   HCD.AdaptativeSpeed,
   HCD.ComboWindow,
   HCD.SpeedUpTrigger,
   HCD.SpeedUpInc,
   HCD.SlowDownTrigger,
   HCD.LowestSpeedFactor,
   HCD.SlowDownDec,
   HCD.MiddlePadding,
   HCD.BaseTimeToShow,
   HCD.Interval,
   HCD.AccuracyRange
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
    pattern = row[1].split('\t')
    patterntime = [float(i) for i in pattern[::2]]
    patternkeys = [int(i)-1 for i in pattern[1::2]]

    return jsonify(
      expNumber=row[0],
      patterntime=patterntime,
      patternkeys=patternkeys,
      showLetters=row[2],
      letterColor=row[3],
      letterSize=row[4],
      numkeys=row[5],
      keys=row[6].split(' '),
      bubbleColor=row[7].split(' '),
      batchSize=row[8],
      adaptativeSpeed=row[9],
      comboWindow=row[10],
      speedUpTrigger=row[11],
      speedUpInc=row[12],
      slowDownTrigger=row[13],
      lowestSpeedFactor=row[14],
      slowDownDec=row[15],
      middlePadding=row[16],
      baseTimeToShow=row[17],
      interval=row[18],
      accuracyRange=row[19],
     )

@app.route('/user/<token>/response/<int:expnumber>', methods=['POST', 'OPTIONS'])
@crossdomain(origin='*', methods=['POST', 'OPTIONS'], headers=['X-Requested-With', 'Content-Type', 'Origin'])
def storeResponse(token, expnumber):
  expNumber = request.json['expNumber']
  batchId = request.json['batchId']
  responses = request.json['responses']
  end = request.json['end']

  # Update experice number if all sequence has been played
  if end:
    newNumber = int(expNumber) + 1
    conn = db.connect(
      host = "mysql-user.stanford.edu",
      user = "gsislhero",
      passwd = "eepulood",
      db = "g_sisl_hero")
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE g_sisl_hero.Hero_User SET ConfigDataNumber=%s WHERE Token=%s
    """, [newNumber, token])
    cursor.close()
    conn.close()

  # Store responses sent
  if len(responses):
    data = [
      (
        x['eventType'],
        token,
        expNumber, 
        x['eventTimestamp'],
        batchId,
        int(time.time() * 1000),
        x['key'],
        1 if x['hit'] else 0,
        x['offset'],
        x['closestKey'],
        x['queuePosition'],
        x['speedFactor'],
        x['speedChange'],
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
    INSERT INTO g_sisl_hero.Hero_ResponseEvent (
      EventType,
      Token,
      ExpNumber,
      EventTimestamp,
      BatchID,
      BatchTimestamp,
      KeyID,
      HitFlag,
      Offset,
      ClosestKeyID,
      QueuePosition,
      SpeedFactor,
      SpeedChange
    )
    VALUES
      (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, data)
    cursor.close()
    conn.close()

  return 'OK'

 
if __name__ == '__main__':
  app.run()
