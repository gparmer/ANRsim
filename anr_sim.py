# Licence is GPLv2.  Please see LICENSE for details.
# Copyright Gabriel Parmer, gparmer@gwu.edu, 2015

#!/usr/bin/python

import sys
import random
import copy
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import scipy.stats

nclicks  = 30
nsamples = 128 # number of simulated games per configuration
decksize = 45
inithand = 5
hist     = False
macroclickperturn = 2

# simply using the discrete event simulator to emulate multiple clicks
def multiclick_apply(state, card):
    card['clicksspent'] = card['clicksspent'] + 1
    if card['clicksspent'] < card['clickcost']:
        add_click_action_card(state, 1, card, multiclick_apply, 5, True)
    return card

default = {'name':'Default', 'drawperclick':0, 'cost':0, 'type':'anonymous', 'clickcost':1, 'clickcreditgain':0, 'creditgain':0, 'draw':0, 'mu':0, 'inplay':False, 'singleuse':True, 'clicksspent':0, 'apply':(lambda s, x: s), 'clickapply':(lambda s, x: s), 'singleton':False, 'dead':False, 'subtypes':[], 'clickupdate':None, 'tutor':None}
draw    = {'name':'Draw', 'drawperclick':1, 'inplay':True, 'singleuse':False, 'type':'program', 'dead':True}
cred    = {'name':'Credit', 'clickcreditgain':1, 'inplay':True, 'singleuse':False, 'type':'program', 'dead':True}
mopus   = {'name':'Magnum Opus', 'clickcreditgain':2, 'cost':5, 'type':'program', 'singleuse':False, 'singleton':True, 'dead':True, 'mu':2}
sg      = {'name':'Sure Gamble', 'cost':5, 'creditgain':9, 'type':'event', 'dead':True}
dj      = {'name':'Day Job', 'cost':2, 'creditgain':10, 'type':'event', 'clickcost':4, 'dead':True, 'apply':multiclick_apply}
lf      = {'name':'Lucky Find', 'cost':3, 'clickcost':2, 'creditgain':9, 'type':'event', 'dead':True, 'apply':multiclick_apply}
dl      = {'name':'Dirty Laundry', 'cost':2, 'creditgain':5, 'type':'event', 'dead':True}
diesel  = {'name':'Diesel', 'draw':3, 'type':'event', 'dead':True}
ss      = {'name':'Steelskin', 'draw':3, 'cost':1, 'type':'event', 'dead':True}
qt      = {'name':'Quality Time', 'draw':5, 'cost':3, 'type':'event', 'dead':True}
pc      = {'name':'Professional Contacts', 'clickcreditgain':1, 'drawperclick':1, 'cost':5, 'type':'resource', 'singleuse':False, 'singleton':True, 'dead':True}

def inj_apply(state, c):
    for i in range(4):
        newc = deck_get(state)
        if newc == None:
            return
        # assume that the default cards are programs...
        if newc['type'] == 'program' or newc['type'] == 'anonymous':
            gain_creds(state, 1)
            state['drawn'] = state['drawn'] + 1
        else:
            board_add_drawn(state, newc)

inj = {'name':'Inject', 'cost':1, 'type':'event', 'dead':True, 'apply':inj_apply}

def earthrisetick(state, card):
    if (card['clicksspent'] < 3):
        draw_cards(state, 2)
        add_click_action_card(state, macroclickperturn, card, earthrisetick, 10, False)
    else:
        trash(state, card)
    card['clicksspent'] = card['clicksspent'] + 1
def earthriseapply(state, card):
    card['priority'] = -10
    add_click_action_card(state, macroclickperturn-1, card, earthrisetick, 10, False)    
eh = {'name':'Earthrise Hotel', 'cost':4, 'type':'resource', 'singleuse':False, 'dead':True, 'apply':earthriseapply}

def pvpmod(state, pvp):
    for c in state['board'] + state['deck']:
        if c['type'] == 'event':
            c['cost'] = max(c['cost']-1, 0)
    return pvp
pvp  = {'name':'Prepaid Voice Pad', 'cost':2, 'type':'hardware', 'apply':pvpmod, 'dead':True}
pvpk = {'name':'Prepaid Voice Pad', 'cost':1, 'type':'hardware', 'apply':pvpmod, 'dead':True}

def trtutor(state, tr):
    c = state['deckprogs'][0]
    card_tutor(state, c)
    def tr_removeprog(state, card):
        state['board'].remove(card)
        state['deck'].append(card)
        state['deckprogs'] = [card] + state['deckprogs']
        card['inplay'] = False
    add_click_action_card(state, 4, c, tr_removeprog, 10, False)
    return tr

def trtutorupdate(state, c):
    assert length(state['deckprogs']) > 0
    p = state['deckprogs'][0]
    c['priority'] = p['priority']
    return
    
tr = {'name':'Test Run', 'cost':3, 'apply':trtutor, 'clickcost':1, 'dead':True, 'type':'event', 'tutor':'program', 'clickupdate':trtutorupdate}

def smctutor(state, smc):
    c = state['deckprogs'][0]
    card_tutor(state, c)
    return smc

def smctutorupdate(state, c):
    assert length(state['deckprogs']) > 0
    p             = state['deckprogs'][0]
    c['priority'] = p['priority']
    c['cost']     = c['cost'] + 2
    return

smc = {'name':'Self-Modifying Code', 'type':'program', 'cost':7, 'apply':smctutor, 'dead':True, 'tutor':'program', 'clickupdate':smctutorupdate}

def shuffle(state):
    random.shuffle(state['deck'])

def reprioritize(state, cards, prio):
    for c in state['deck'] + state['board']:
        for deprio in cards:
            if c['name'] == deprio:
                c['priority'] = prio

def deprioritize(state, cards):
    reprioritize(state, cards, -10)

# BUG: multiple singletons pulled into hand at once (in starting hand, or via draw) are counted as quality draws
def make_dead(state, cards):
    deprioritize(state, cards)
    for c in state['deck'] + state['board']:
        for d in cards:
            if c['name'] == d:
                c['dead'] = True

# fill out all fields in a card structure with default data
def card_data(meta, priority):
    m = default.copy()
    for k in m.keys():
        if k in meta:
            m[k] = meta[k]
    m['priority'] = priority
    return m

def find_card(state, name):
    for c in state['board']:
        if c['name'] == name:
            return c
    return None

def deck_get(state):
    if len(state['deck']) == 0:
        c = find_card(state, 'Draw')
        if c != None:
            state['board'].remove(c)
        return None
    c = state['deck'].pop()
    if c in state['deckprogs']:
        state['deckprogs'].remove(c)
    return c

def board_add_drawn(state, newc):
    state['board'].append(newc)
    if newc['dead'] == False:
        state['qdrawn'] = state['qdrawn'] + 1
    state['drawn'] = state['drawn'] + 1
    
def draw_cards(state, ncards):
    for i in range(ncards):
        newc = deck_get(state)
        if newc == None:
            return
        board_add_drawn(state, newc)

def gain_creds(state, ncreds):
    state['creds'] = state['creds'] + ncreds
    
def card_use(c, state):
    gain_creds(state, c['clickcreditgain'])
    draw_cards(state, c['drawperclick'])
    c['clickapply'](state, c)

def card_playable(state, c):
    return state['creds'] >= c['cost']

def deck_remove(state, c):
    assert len([x for x in state['deck'] if x == c]) > 0
    state['deck'].remove(c)
    state['deckprogs'].remove(c)

def discard(state, c):
    assert len([x for x in state['board'] if x == c]) > 0
    state['board'].remove(c)
    state['discard'].append(c)

def trash(state, c):
    if c['inplay']:
        c['inplay'] = False
    discard(state, c)
    
def card_activate(state, c, pay):
    assert not c['inplay']
    if c['singleuse']:
        discard(state, c)
    else:
        c['inplay'] = True
    assert card_playable(state, c)
    if pay:
        gain_creds(state, -1 * c['cost'])
    gain_creds(state, c['creditgain'])
    draw_cards(state, c['draw'])
    c['apply'](state, c)
    prio = c['priority']
    if c['singleton']:
        make_dead(state, [c['name']])
    c['priority'] = prio

def card_play(state, c):
    card_activate(state, c, True)

def card_tutor(state, c):
    deck_remove(state, c)
    card_activate(state, c, False)
    shuffle(state)

def find_money(state):
    board = state['board']
    for c in board:
        if c['inplay'] == True and c['clickcreditgain'] > 0:
            return c
        if c['cost'] <= state['creds'] and c['creditgain'] > 0:
            assert card_playable(state, c)
            return c
    print "Error:  Could not find any money in:"
    print board
    return None

def prio_sort(a, b):
    if a['priority'] > b['priority']:
        return -1
    elif a['priority'] == b['priority'] and ((a['cost'] < b['cost'] and a['creditgain'] > 0) or (b['tutor'] != None)):
        return -1
    else:            
        return 1

def normal_click(state):
    board = state['board']
    board.sort(prio_sort)
    c = board[0]
    while True:
        assert c['name'] != "Default"
        if not c['inplay']:
            if card_playable(state, c):
                card_play(state, c)
            else:
                c = find_money(state)
                assert card_playable(state, c) or c['inplay']
                continue
        else:
            card_use(c, state)
        break
    return c

def action_sort(a, b):
    (fa, pa, ca) = a
    (fb, pb, cb) = b
    if pa <= pb:
        return -1
    return 1
    
def add_click_action(state, clickno, fn, prio, needs_click):
    newclk = state['click'] + clickno
    assert newclk > state['click']
    if newclk >= nclicks:
        return
    clicks = state['clicks']
    clicks[newclk].append((fn, prio, needs_click))

def add_click_action_card(state, clickno, card, fn, prio, needs_click):
    add_click_action(state, clickno, lambda s: fn(s, card), prio, needs_click)

def click(state):
    actions = state['clicks'][state['click']]
    for c in state['board']:
            if c['clickupdate'] != None:
                    c['clickupdate'](state, c)
    actions.sort(action_sort)
    clickused = False
    while len(actions) > 0:
        (fn, prio, needs_click) = actions.pop()
        if needs_click:
            if clickused:
                continue
            clickused = True
        c = fn(state)
        if needs_click:
            state['history'].append({'card':c, 'drawn':state['drawn'], 'qdrawn':state['qdrawn'], 'creds':state['creds']})

    state['click'] = state['click'] + 1

def history_print(state):
    print "Hist\tClick\tCreds\tDraw\tQDraw\tName"
    cnt = 1
    for h in state['history']:
        print "\t" + str(cnt) + "\t" + str(h['creds']) + "\t" + str(h['drawn']) + "\t" + str(h['qdrawn']) + "\t" + h['card']['name']
        cnt = cnt + 1

def generate_def_clicks():
    clicks = []
    for i in range(0, nclicks):
        clicks.append([])
        clicks[i].append((normal_click, 0, True))
    return clicks

def starting_hand(_deck, ncards, mulfn):
    for mul in [0, 1]:
        deck = copy.deepcopy(_deck)
        random.shuffle(deck)
        board = copy.deepcopy(defboard)
        for i in range(ncards):
            board.append(deck.pop())
        if not mulfn(board):
            break
    return (deck, board)

def game(_deck, nclicks, mulfn, inithandsz):
    (deck, board) = starting_hand(_deck, inithandsz, mulfn)
    draw = 0
    for c in board:
        if not c['dead']:
            draw = draw + 1
    clicks = generate_def_clicks()
    progs  = [c for c in deck if c['type'] == 'program']
    progs.sort((lambda a, b: -1 if a['priority'] > b['priority'] else 1))
    state  = {'board':board, 'deck':deck, 'deckprogs':progs, 'creds':5, 'drawn':inithandsz, 'qdrawn':draw, 'mu':4, 'history':[], 'discard':[], 'click':0, 'clicks':clicks}
    while state['click'] < nclicks:
        click(state)
    return state

defboard = [card_data(cred, -2), card_data(draw, -1)]

def game_exec(d, mulfn, inithandsz):
    results = []
    cs      = []
    ds      = []
    qds     = []

    for i in range(nsamples):
        output = game(d, nclicks, mulfn, inithandsz)
        results.append(output['history'])
        if hist:
            history_print(output)

    for i in range(nclicks):
        cluster = []
        draw    = []
        qdraw   = []
        for r in results:
            cluster.append(r[i]['creds'])
            draw.append(r[i]['drawn'])
            qdraw.append(r[i]['qdrawn'])
        cs.append(cluster)
        ds.append(draw)
        qds.append(qdraw)
    return cs,ds,qds

# Plotting functions:

# take the derivative of discrete samples, and smooth it over three
# samples
def derivative_fn(arr):
    new = []
    assert len(arr) > 3
    new.append(0)
    for i in range(1, len(arr)-1):
        new.append(((arr[i] - arr[i-1]) + (arr[i+1] - arr[i]))/2)
    new.append(new[len(arr)-2])
    assert len(new) == len(arr)
    return new

# Ugh, a combinatorial explosion in the conditions...
def plot_game(creds, drawn, qdrawn, option, deriv, c, l):
    arr  = np.array(creds)
    qds  = np.array(qdrawn)
    #ress = np.add(arr, qds)
    ress = arr + qds
    ds   = np.array(drawn)
    np.sort(arr)
    if option == "mean":
        mean = np.mean(arr, axis=1)
        if deriv:
            mean = derivative_fn(mean)
        plt.plot(range(nclicks), mean, c, label=l, linewidth=3)
    elif option == "stddev":
        std  = np.std(arr, axis=1)
        if deriv:
            std = derivative_fn(std)
        plt.plot(range(nclicks), std, c, label=l, linewidth=3)
    elif option == "90p":
        ninety = []
        for i in range(nclicks):
            val = copy.copy(arr[i])
            val.sort()
            assert len(val) == nsamples
            idx = int(float(nsamples)*0.1)
            assert val[idx-1] <=  val[idx] <= val[idx+1]
            # smooth the value over 20 iterations
            ninety.append(np.mean(val[idx-10:idx+10]))

        if deriv:
            ninety = derivative_fn(ninety)
        plt.plot(range(nclicks), ninety, c, label=l, linewidth=3)
    elif option == "res":
        mean = np.mean(ress, axis=1)
        if deriv:
            mean = derivative_fn(mean)
        plt.plot(range(nclicks), mean, c, label=l, linewidth=3)
    elif option == "draw" or option == 'qdraw':
        if option == 'draw':
            mean = np.mean(drawn, axis=1)
        else:
            mean = np.mean(qdrawn, axis=1)
        if deriv:
            mean = derivative_fn(mean)
        plt.plot(range(nclicks), mean, c, label=l, linewidth=3)
    else:
        print "Wrong options to plot!"
    if not deriv:
        if option != 'draw' and option != 'qdraw':
            if option != 'stddev':
                plt.plot(range(nclicks), map(lambda x: 5 + x, range(nclicks)), "k:")
                plt.plot(range(nclicks), map(lambda x: 5 + 2*x, range(nclicks)), "k:", color="#777777")
        else:
            plt.plot(range(nclicks), map(lambda x: 5 + x, range(nclicks)), "k:")
    if option == "mean" or option == "90p" or option == "stddev":
        if deriv:
            plt.ylabel("Credits/Click")
        else:
            plt.ylabel("Credits")
    elif option == "res":
        if deriv:
            plt.ylabel("(Credits+Quality Draws)/Click")
        else:
            plt.ylabel("Credits+Quality Draws")
    else:
        if deriv:
            plt.ylabel("Useful Cards/Click")
        else:
            plt.ylabel("Useful Cards")
    plt.xlabel("Clicks")
    translation = [('mean', 'Credits'), ('qdraw', 'Quality Draws'), ('draw', 'Draws'), ('90p', 'Credits for the 10th percentile of Games'), ('stddev', 'Credit Standard Deviation'), ('res', 'Resources Gained (Credits + Quality Draw)')]
    name = option
    for (o, n) in translation:
        if o == option:
            name = n
            break
    plt.title(name)
    plt.grid(True)

def percentile(percent, creds):
    ninety = []
    for i in range(nclicks):
        val = copy.copy(creds[i])
        val.sort()
        assert len(val) == nsamples
        idx = int(float(nsamples)*percent)
        assert val[idx-1] <=  val[idx] <= val[idx+1]
        # smooth the value over 20 iterations
        ninety.append(np.mean(val[idx-10:idx+10]))
    return ninety
    
def plot_deck(sp, creds, drawn, qdrawn, format, _label):
    arr  = np.array(creds)
    qds  = np.array(qdrawn)
    #ress = np.add(arr, qds)
    ress = arr + qds
    ds   = np.array(drawn)
    np.sort(arr)

    mean  = np.mean(arr, axis=1)
    meand = derivative_fn(mean)

    dmean = np.mean(drawn, axis=1)
    qmeand = derivative_fn(qmean)
    qdmean = np.mean(qdrawn, axis=1)
    qdmeand = derivative_fn(qdmean)
    
    res  = np.mean(ress, axis=1)
    resd = derivative_fn(res)

    std  = np.std(arr, axis=1)

    ten        = percentile(0.1)
    twentyfive = percentile(0.25)
    fifty      = percentile(0.5)

    sp[0,0].plot(range(nclicks), mean, format, label=_label, linewidth=3)
    sp[1,0].plot(range(nclicks), meand, format, label=_label, linewidth=3)

    sp[0,1].plot(range(nclicks), qdmean, format, label=_label, linewidth=3)
    sp[1,1].plot(range(nclicks), qdmeand, format, label=_label, linewidth=3)    

    sp[0,2].plot(range(nclicks), res, format, label=_label, linewidth=3)
    sp[1,2].plot(range(nclicks), resd, format, label=_label, linewidth=3)

    sp[2,0].plot(range(nclicks), fifty, format, label=_label, linewidth=3)
    sp[2,1].plot(range(nclicks), twentyfive, format, label=_label, linewidth=3)
    sp[2,2].plot(range(nclicks), ten, format, label=_label, linewidth=3)    
    
def plot_defaults(sp):
    for i in range(3):
        sp[0,i].plot(range(nclicks), map(lambda x: 5 + x, range(nclicks)), "k:")
        sp[0,i].plot(range(nclicks), map(lambda x: 5 + 2*x, range(nclicks)), "k:", color="#777777")
    for i in range(3):
        sp[1,i].plot(range(nclicks), [1] * nclicks, "k:")
        sp[1,i].plot(range(nclicks), [2] * nclicks, "k:", color="#777777")
    for i in range(1,3):
        sp[0,i].plot(range(nclicks), map(lambda x: 5 + x, range(nclicks)), "k:")
    sp[0,0].set_title('Credits')
    sp[0,1].set_title('Quality Draws')
    sp[0,2].set_title('Resources')
    sp[1,0].set_title('Credits/Click')
    sp[1,1].set_title('Quality Draws/Click')
    sp[1,2].set_title('(Creds+Quality Draws)/Click')
    sp[2,0].set_title('Credits: 50% Game')
    sp[2,1].set_title('25% Game')
    sp[2,2].set_title('10% Game')
    for i in range(3):
        sp[2,i].set_xlabel('Clicks')
    
def plot_alldecks(creds, drawns, qdrawns, formats, labels):
    f, sp = plt.subplots(3, 3)
    plot_defaults(sp)
    #for cs, ds, qds, fmt, lbl in zip(creds, drawns, qdrawns, formats, labels):
    #plot_deck(sp, cs, ds, qds, fmt, lbl)
    for i in range(3):
        for j in range(3):
            sp[i,j].plot()
    lgd = sp[2,1].legend(loc=9, bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=3)
    art = []
    art.append(lgd)
    plt.grid(True)
    plt.savefig('all.png', additional_artists=art, bbox_inches="tight")
        
def copies(c, prio, ncpys):
    return [copy.deepcopy(card_data(c, prio)) for nop in range(ncpys)]

# Common configurations
def evtsdj():
    return evts() + copies(dj, 7, 3)
def evtsdjnlf():
    return copies(sg, 6,3) + copies(dl, 5,3) + copies(dj, 7, 3)
def evts():
    return copies(sg, 6,3) + copies(dl, 5,3) + copies(lf, 8,3)
def evtsnlf():
    return copies(sg, 6,3) + copies(dl, 5,3)
def draweh():
    return draw() + copies(eh, 3, 3)
def draw():
    return copies(diesel, 4, 3) + copies(qt, 3, 3)
def anarchdraw():
    return copies(inj, 4, 3) + copies(ss, 3, 3)
def anarchdraweh():
    return anarchdraw() + copies(eh, 3, 3)
def tutors():
    return copies(tr, 5, 3) + copies(smc, 6, 3)

def pad_deck(cards, sz):
    l = len(cards)
    assert sz > l
    return cards + copies(default, -10, sz-l)

def mulgen(hand, cs):
    mul = True
    for c in hand:
        for s in cs:
            if c['name'] == s:
                mul = False
    return mul

def opusmul(hand):
    return mulgen(hand, ['Magnum Opus'])

def evtmul(hand):
    return mulgen(hand, ['Sure Gamble', 'Lucky Find'])

def drawmul(hand):
    return mulgen(hand, ['Diesel'])

def proconsmul(hand):
#    return evtmul(hand)
    return mulgen(hand, ['Professional Contacts'])

# article one: event econs
inputs1 = [
    (pad_deck(evts(), decksize), evtmul, inithand, "g--", "evts"),
    (pad_deck(evts() + draw(), decksize), evtmul, inithand, "g", "evts+draw"),
    (pad_deck(evts() + draw() + copies(pvp, 9,3), decksize), evtmul, inithand, "y", "pvp+evts+draw"),
    (pad_deck(evts() + draw() + copies(pvpk, 9,3), decksize), evtmul, inithand, "y--", "kate:pvp+evts+draw"),
    (pad_deck(copies(pc, 2,3), decksize), proconsmul, inithand, "b--", "procons"),    
    (pad_deck(evts() + copies(pc, 2,3), decksize), proconsmul, inithand, "b", "evts+procons")
    ]

# article two
inputs2a = [(pad_deck(evts() + draw(), decksize), evtmul, inithand, "r", "evts+draw"),
    (pad_deck(evtsnlf() + draw(), decksize), evtmul, inithand, "r--", "oldevts+draw"),
    (pad_deck(copies(pvpk, 9,3) + evts() + draw(), decksize), evtmul, inithand, "y", "kate:pvp+evts+draw"),
    (pad_deck(copies(pvpk, 9,3) + evtsnlf() + draw(), decksize), evtmul, inithand, "y--", "kate:pvp+oldevts+draw")
    ]

inputs2b = [(pad_deck(evtsdj() + draweh(), decksize), evtmul, inithand, "g", "evts+DJ+draw+EH"),
    (pad_deck(evtsdj() + draw(), decksize), evtmul, inithand, "b", "evts+DJ+draw"),
    (pad_deck(evts() + draweh(), decksize), evtmul, inithand, "g--", "evts+draw+EH"),
    (pad_deck(evts() + draw(), decksize), evtmul, inithand, "b--", "evts+draw"),
    (pad_deck(evts() + copies(pc, 2,3), decksize), proconsmul, inithand, "r", "evts+procons")            
    ]

inputs2c = [(pad_deck(evtsdj() + draw() + copies(pvpk, 4, 3), decksize), evtmul, inithand, "b", "kate:pvp+evts+DJ+draw"),
    (pad_deck(evtsdjnlf() + draw() + copies(pvpk, 4, 3), decksize), evtmul, inithand, "r", "kate:pvp+evts+DJ-LF+draw"),
    (pad_deck(evtsdjnlf() + copies(pc, 2,3), decksize), proconsmul, inithand, "g", "evts-LF+DJ+procons"),
    (pad_deck(evts() + draw(), decksize), evtmul, inithand, "y:", "evts+draw"),
    (pad_deck(evts() + copies(pc, 2,3), decksize), proconsmul, inithand, "y--", "evts+procons"),
    (pad_deck(copies(pvpk, 4, 3) + evts() + draw(), decksize), evtmul, inithand, "y", "pvp+evts+draw")
    ]

# article three
inputs3a = [(pad_deck(evtsdj() + anarchdraweh(), decksize), evtmul, inithand, "b", "evts+DJ+adraw+EH"),
            (pad_deck(evtsdjnlf() + anarchdraweh(), decksize), evtmul, inithand, "b--", "evts-LF+DJ+adraw+EH"),
            (pad_deck(evtsdj() + anarchdraw(), decksize), evtmul, inithand, "g", "evts+DJ+adraw"),
            (pad_deck(evtsdjnlf() + anarchdraw(), decksize), evtmul, inithand, "g--", "evts-LF+DJ+adraw"),
            (pad_deck(evtsdj() + draw(), decksize), evtmul, inithand, "y", "evts+DJ+draw"),
            (pad_deck(evts() + draw(), decksize), evtmul, inithand, "y--", "evts+draw"),
            ]

inputs3b = [(pad_deck(evtsdj() + anarchdraweh() + copies(pvp, 4, 3), decksize), evtmul, inithand, "b", "pvp+evts+DJ+adraw+EH"),
            (pad_deck(evtsdjnlf() + anarchdraweh() + copies(pvp, 4, 3), decksize), evtmul, inithand, "b--", "pvp+evts-LF+DJ+adraw+EH"),
            (pad_deck(evtsdj() + anarchdraw() + copies(pvp, 4, 3), decksize), evtmul, inithand, "g", "pvp+evts+DJ+adraw"),
            (pad_deck(evtsdjnlf() + anarchdraw() + copies(pvp, 4, 3), decksize), evtmul, inithand, "g--", "pvp+evts-LF+DJ+adraw"),
            (pad_deck(evtsdj() + draw() + copies(pvpk, 4, 3), decksize), evtmul, inithand, "y", "katepvp+evts+DJ+draw"),
            (pad_deck(evts() + draw() + copies(pvpk, 4, 3), decksize), evtmul, inithand, "y--", "katepvp+evts+draw"),
            ]

# article four
inputs4 = [((copies(mopus,10,3) + copies(default,-10,42)), opusmul, inithand, "#3366ff", "opus"),
    (pad_deck(copies(mopus,10,3) + tutors() + draw(), decksize), opusmul, inithand, "#0000ff", "opus+draw+tutors"),
    (pad_deck(evts() + draw(), decksize), evtmul, inithand, "g", "evts+draw"),
    (pad_deck(evts() + draw() + copies(pvpk, 9,3), decksize), evtmul, inithand, "y--", "kate:pvp+evts+draw")
    ]

if len(sys.argv) > 1:
    if sys.argv[1] == '-v':
        hist = True

inputs = inputs3a
games   = []
creds   = []
draws   = []
qdraws  = []
formats = []
labels  = []
for i in range(len(inputs)):
    c, d, qd = game_exec(inputs[i][0], inputs[i][1], inputs[i][2])
    games.append((c, d, qd, inputs[i][3], inputs[i][4]))
    creds.append(c)
    draws.append(d)
    qdraws.append(qd)
    formats.append(inputs[i][3])
    labels.append(inputs[i][4])

plot_alldecks(creds, draws, qdraws, formats, labels)

# plt.clf() # clear the output
# for outputtype in ['mean', 'stddev', '90p', 'draw', 'qdraw', 'res']:
#     for deriv in [False, True]:
#         for (c, d, qd, plottype, name) in games:
#             plot_game(c, d, qd, outputtype, deriv, plottype, name)
#         if deriv:
#             plt.legend(loc='lower right')
#             derivative = 1
#         else:
#             plt.legend(loc='upper left')
#             derivative = 0
#             if outputtype == 'draw' or outputtype == 'qdraw':
#                 plt.axis([0,29,0,30])
#             else:
#                 plt.axis([0,29,0,40])
#         plt.savefig(outputtype + str(derivative) + '.png')
#         plt.clf() # clear the output
# #plt.show()
