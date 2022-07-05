from curses import raw
import selenium
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium import webdriver
import time
import pandas as pd
import numpy as np

def per_hole_scoring(score):
    '''
    Double Eagle or Better = 13
    Eagle = 8
    Birdie = 3
    Par = 0.5
    Bogey = -0.5
    Double Bogey = -1
    Worse than Double Bogey = -1
    '''
    pts = 0
    for rh in score:
        if rh == -3:
            p = 13
        elif rh == -2:
            p = 8
        elif rh == -1:
            p = 3
        elif rh == 0:
            p = 0.5
        elif rh == 1: 
            p = -0.5
        else:
            p = -1
        pts += p
    return pts

def streaks_and_bonuses(r1, r2, r3, r4, par):
    '''
    Streak of 3 birdies or better = 3
    Bogey Free Round = 3
    All 4 Rounds Under 70 Strokes = 5
    '''

    if r3 is not None:
        tot1 = par + sum(r1)
        tot2 = par + sum(r2)
        tot3 = par + sum(r3)
        tot4 = par + sum(r4)
        r_array = [r1, r2, r3, r4]

        if tot1 < 70 and tot2 < 70 and tot3 < 70 and tot4 < 70:
            under_70_pts = 5
        else:
            under_70_pts = 0
    else:
        tot1 = par + sum(r1)
        tot2 = par + sum(r2)
        r_array = [r1, r2]

        if tot1 < 70 and tot2 < 70:
            under_70_pts = 5
        else:
            under_70_pts = 0
    
    bogey_free = 0
    for r in r_array:
        for h in r:
            if h > 0:
                bogey_streak_pts = 0
                break
            else:
                bogey_streak_pts = 3
        bogey_free += bogey_streak_pts
    
    birdie_streak = 0
    for r in r_array:
        l1 = False
        l2 = False
        for h in r:
            if h < 0 and l1 == False:
                l1 = True
            elif h < 0 and l1 == True and l2 == False:
                l2 = True
            elif h < 0 and l1 == True and l2 == True:
                birdie_streak += 3
                l1 = False
                l2 = False
            else:
                l1 = False
                l2 = False
    return bogey_free + birdie_streak + under_70_pts

def hole_in_one(score):
    hi1 = 0
    for s in score:
        if s == 1:
            hi1 += 5
    return hi1


def place_points(place):
    '''
    1st = 30
    2nd = 20
    3rd = 18
    4th = 16
    5th = 14
    6th = 12
    7th = 10
    8th = 9
    9th = 8
    10th = 7
    11 - 15 = 6
    16 - 20 = 5
    21 - 25 = 4
    26 - 30 = 3
    31 - 40 = 2
    41 - 50 = 1
    '''
    if place == 1:
        pts = 30
    elif place == 2:
        pts = 20
    elif place == 3:
        pts = 18
    elif place == 4:
        pts = 16
    elif place == 5:
        pts = 14
    elif place == 6:
        pts = 12
    elif place == 7:
        pts = 10
    elif place == 8:
        pts = 9
    elif place == 9:
        pts = 8
    elif place == 10:
        pts = 7
    elif place < 16:
        pts = 6
    elif place < 21:
        pts = 5
    elif place < 26:
        pts = 4
    elif place < 31:
        pts = 3
    elif place < 41:
        pts = 2
    elif place < 51:
        pts = 1
    else:
        pts = 0
    return pts
    
def pos_rewrite(x: str):
    '''A function that converts a position from a str to an integer, including ties'''
    data = x.split(' ')
    pos = data[-1]
    if pos[0] == 'T':
        pos = int(pos[1:])
    elif pos == 'CUT':
        pos = 100
    else:
        try:
            pos = int(pos)
        except:
            pos = np.nan
    return pos

def find_par(df):
    winner = df.iloc[0]
    par = (int(winner['TOT']) - int(winner['SCORE'])) / 4
    return par

def find_net_score(df_score):
    try:
        hole = np.arange(0,18,1)
        par = df_score.iloc[0].values
        score = df_score.iloc[1].values
        r_net_score = []
        for h in hole:
            h_score = score[h] - par[h]
            r_net_score.append(h_score)
    except:
        r_net_score = None
    return r_net_score

def round_dk_score(r1_score, r2_score, r3_score, r4_score, pos, par):
    '''

    '''
    

    tot_pts = 0
    if r3_score is not None:
        tournament_score = [r1_score, r2_score, r3_score, r4_score]
    else:
        tournament_score = [r1_score, r2_score]
    for r_score in tournament_score:
        tot_pts += per_hole_scoring(find_net_score(r_score))
        tot_pts += hole_in_one(r_score)

    # print(f'player points score: {place_points(pos)}')
    # print(f'streaks and bonuses: {streaks_and_bonuses(find_net_score(r1_score), find_net_score(r2_score), find_net_score(r3_score), find_net_score(r4_score), par)}')
    tot_pts += place_points(pos)
    tot_pts += streaks_and_bonuses(find_net_score(r1_score), find_net_score(r2_score), find_net_score(r3_score), find_net_score(r4_score), par)
    return tot_pts
    

def round_scores(driver, select2, round):
    select2.select_by_visible_text(round)
    scores = driver.page_source
    scores_pd = pd.read_html(scores)
    df_scores = scores_pd[1]
    df_scores = df_scores.drop(['Hole', 'Out', 'In', 'Tot'], axis=1)

    return df_scores


#MAIN

#USER INPUT
url = "https://www.espn.com/golf/leaderboard?tournamentId=401353220"
##

driver = webdriver.Firefox()

raw_data = pd.read_html(url)
raw_data = raw_data[-1]

raw_data['POS'] = raw_data['POS'].apply(lambda x: pos_rewrite(x))
raw_data = raw_data.drop(['EARNINGS', 'FEDEX PTS'], axis=1)
par = find_par(raw_data)
driver.get(url)
df_total_points = pd.DataFrame(columns=["Name", "DK Score"])

for index, row in raw_data.iterrows():
    print(df_total_points.head())
    player = row['PLAYER']
    pos = row["POS"]
    print(pos)

    # get element 
    element = driver.find_element(By.XPATH, f'// a[contains(text(), "{player}")]')

    # click the element
    element.click()
    driver.implicitly_wait(120)
    time.sleep(2)
    
    try:
        select = driver.find_element(By.CLASS_NAME, 'Leaderboard__Player__Detail')
        select2 = Select(select.find_element(By.CLASS_NAME, 'dropdown__select'))
        if pos < 100:
            r1 = round_scores(driver, select2, "Round 1")
            r2 = round_scores(driver, select2, "Round 2")
            r3 = round_scores(driver, select2, "Round 3")
            r4 = round_scores(driver, select2, "Round 4")
        else:
            r1 = round_scores(driver, select2, "Round 1")
            r2 = round_scores(driver, select2, "Round 2")
            r3 = None
            r4 = None
        row = {"Name": row['PLAYER'], "DK Score" : round_dk_score(r1, r2, r3, r4, pos, par)}
    except:
        row = {"Name": row['PLAYER'], "DK Score" : 0}


    df_total_points = df_total_points.append(row, ignore_index=True)
    #print(f'{row["PLAYER"]} dk score: {round_dk_score(r1, r2, r3, r4, pos, par)}')
    
    
    element.click()

df_total_points.to_csv('total_dk_points_test.csv', index=False)
driver.close()
driver.quit() 
##