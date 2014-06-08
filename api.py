from flask import Flask, jsonify, request
from crossdomain import crossdomain
import logging
import ConfigParser
logging.basicConfig(filename='sisl-server.log',level=logging.DEBUG)

import MySQLdb as db

app = Flask(__name__)
app.debug = False

config = ConfigParser.ConfigParser()
config.read("app.conf")

@app.route('/user/<token>/challenge', methods=['GET', 'OPTIONS'])
@crossdomain(origin='*', methods=['GET', 'OPTIONS'], headers=['X-Requested-With', 'Content-Type', 'Origin'])
def sendChallenge(token):
  logging.debug('Token: ' + token + ' - Asking for a config')
  conn = db.connect(
    host = config.get("DB", "host"),
    user = config.get("DB", "user"),
    passwd = config.get("DB", "passwd"),
    db = config.get("DB", "db")
  )

  # First get the list of cues
  cursor = conn.cursor()
  cursor.execute("""
  SELECT
    TLE.event_id, 
    TLE.cue_id, 
    TLE.event_type,
    TLE.event_value,
    TLE.dist_norm,
    TLE.duration_time_ms,
    TLE.event_category,
    TLE.time_to_target_ms
  FROM        user U
  INNER JOIN  scenario_list SL
  ON          (
                U.scenario_list_id = SL.scenario_list_id AND 
                U.scenario_list_position = SL.scenario_list_position
              )
  INNER JOIN  scenario S
  ON          (
                S.scenario_id = SL.scenario_id
              )
  INNER JOIN  trial_list_event TLE
  ON          (
                TLE.trial_list_id = S.trial_list_id
              )
  WHERE       U.user_token = %s
  ORDER BY    TLE.event_id
  """, [token])
  
  events = []
  for row in cursor.fetchall():
    events.append({
      'eventId': row[0],
      'cueId': row[1],
      'type': row[2],
      'value': int(row[3]) if row[2] == 'cue' else row[3],
      'dist': row[4],
      'duration': row[5],
    })
  cursor.close()

  events = sorted(events, key=lambda x: int(x['eventId']))

  logging.debug('Token: ' + token + ' - First part done')

  # then get the parameters
  cursor = conn.cursor()
  cursor.execute("""
  SELECT
    S.scenario_id,
    P.middle_padding,
    P.letter_show,
    P.letter_color,
    P.letter_size,
    P.keys,
    P.num_keys,
    P.cue_colors,
    P.cue_size,
    P.pos_color,
    P.neg_color,
    P.ratio_bubble,
    P.batch_size,
    P.interval,
    P.speed_lookback,
    P.speed_fraction,
    P.speed_up_threshold,
    P.speed_down_threshold,
    P.time_to_elapse,
    P.target_offset,
    P.target_buffer
  FROM        user U
  INNER JOIN  scenario_list SL
  ON          (
                U.scenario_list_id = SL.scenario_list_id AND 
                U.scenario_list_position = SL.scenario_list_position
              )
  INNER JOIN  scenario S
  ON          (
                S.scenario_id = SL.scenario_id
              )
  INNER JOIN  parameter P
  ON          (
                P.parameter_id = S.parameter_id
              )
  WHERE       U.user_token = %s
  """, [token])
  
  row = cursor.fetchone()
  cursor.close()
  conn.close()
  
  logging.debug('Token: ' + token + ' - Second part done')

  response = jsonify(
    scenario=row[0],
    middlePadding=row[1],
    showLetters=row[2],
    letterColor=row[3],
    letterSize=row[4],
    keys=row[5].split(' '),
    numkeys=row[6],
    bubbleColor=row[7].split(' '),
    circleSize=row[8],
    GoodColor=row[9],
    BadColor=row[10],
    ratioBubble=row[11],
    batchSize=row[12],
    adaptativeSpeed=True,
    comboWindow=row[14],
    speedRatio=row[15],
    speedUpTrigger=row[16],
    speedDownTrigger=row[17],
    interval=row[13],
    baseTimeToShow=row[18],
    accuracyOffset=row[19],
    accuracyRange=row[20],
    events=events,
  )
  
  return response

@app.route('/user/<token>/create', methods=['POST', 'OPTIONS'])
@crossdomain(origin='*', methods=['POST', 'OPTIONS'], headers=['X-Requested-With', 'Content-Type', 'Origin'])
def createToken(token):
  try:
    logging.debug('Creating Token: ' + token)
    conn = db.connect(
      host = config.get("DB", "host"),
      user = config.get("DB", "user"),
      passwd = config.get("DB", "passwd"),
      db = config.get("DB", "db")
    )
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO `g_sisl_hero`.`user`
    (
    `user_token`,
    `firstname`,
    `lastname`,
    `overeighteen`,
    `email`,
    `scenario_list_id`,
    `scenario_list_position`,
    `training_progress`,
    `authorization_progress`)
    VALUES (
    %s,
    'Unknown',
    'Unknown',
    1,
    'Unknown',
    2,
    1,
    0,
    0);
    """, [token])
    conn.commit()
    cursor.close()
    conn.close()

    return 'OK'
  except Exception as e:
    logging.error(e)
 
@app.route('/user/<token>/response', methods=['POST', 'OPTIONS'])
@crossdomain(origin='*', methods=['POST', 'OPTIONS'], headers=['X-Requested-With', 'Content-Type', 'Origin'])
def storeResponse(token):
  try:
    scenario = int(request.json['scenario'])
    batchId = request.json['batchId']
    responses = request.json['responses']
    end = request.json['end']

    # Update experice number if all sequence has been played
    if end:
      scenario = scenario + 1
      conn = db.connect(
        host = config.get("DB", "host"),
        user = config.get("DB", "user"),
        passwd = config.get("DB", "passwd"),
        db = config.get("DB", "db")
      )
      cursor = conn.cursor()
      cursor.execute("""
      UPDATE user SET training_progress=1 WHERE user_token=%s
      """, [token])
      conn.commit()
      cursor.close()
      conn.close()

    # Store responses sent
    if len(responses):
      data = [
        (
          token,
          scenario,
          batchId,
          x['cueId'],
          x['eventTimestamp'],
          x['eventType'],
          x['eventValue'],
          x['eventDist'],
          x['eventSpeed']
        )
        for x in responses
      ]

      logging.debug('Token: ' + token + ' - Storing ' + str(len(data)))
      conn = db.connect(
        host = config.get("DB", "host"),
        user = config.get("DB", "user"),
        passwd = config.get("DB", "passwd"),
        db = config.get("DB", "db")
      )
      cursor = conn.cursor()
      cursor.executemany("""
      INSERT INTO output_response (
        user_token,
        scenario_id,
        batch_id,
        cue_id,
        event_time_ms,
        response_type,
        response_value,
        response_dist_norm,
        response_speed
      )
      VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s, %s)
      """, data)
      conn.commit()
      cursor.close()
      conn.close()

    return 'OK'
  except Exception as e:
    logging.error(e)
 
if __name__ == '__main__':
  app.run()
