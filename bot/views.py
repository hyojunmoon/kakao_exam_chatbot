from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import pandas as pd
import os
import pickle
import random

WAIT = False

def keyboard(request):
    return JsonResponse({'type' : 'text'})

def find_func(content):
    return lambda x: content.find(x) != -1

def load_data(user_key):
    if 'user_data.pickle' in os.listdir('.'):
        with open('./user_data.pickle', 'rb') as file:
            data_dic = pickle.load(file)
        if user_key not in data_dic.keys():
            data_dic = {}
            data_dic[user_key] = {'game_start': 0}
            data_dic[user_key]['game_mode'] = '.'
        return data_dic
    else:
        data_dic = {}
        data_dic[user_key] = {'game_start' : 0}
        data_dic[user_key]['game_mode'] = '.'
        return data_dic

def save_data(data_dic):
    global WAIT
    with open('./user_data.pickle', 'wb') as file:
        pickle.dump(data_dic, file, protocol=pickle.HIGHEST_PROTOCOL)
    WAIT = False

def do_game(content, game_name, data_dic, user_key, reverse=False):
    df = pd.read_excel('./data/'+game_name+'.xlsx', header=None)
    total_list = df.index.values.tolist()
    output = ""
    if reverse:
        q, a = 1, 0
    else:
        q, a = 0, 1

    if game_name+'_done' not in data_dic[user_key].keys():
        data_dic[user_key][game_name+'_done'] = []
        data_dic[user_key][game_name+'_q'] = -1
        output += "게임을 시작할게. 총 문제수는 " + str(len(total_list)) + "개야." + '\n\n'

    for i in data_dic[user_key][game_name+'_done']:
        total_list.remove(i)

    if content.find('임시') != -1 and content.find('종료') != -1:
        data_dic[user_key]['game_start'] = 0
        save_data(data_dic)
        return JsonResponse({
            'message': {
                'text': '게임을 임시로 종료할게.'
            },
            'keyboard': {
                'type': 'text'
            }
        })

    if content.find('종료') != -1:
        data_dic[user_key]['game_start'] = 0
        data_dic[user_key]['game_mode'] = '.'
        del data_dic[user_key][game_name+'_done']
        del data_dic[user_key][game_name+'_q']
        save_data(data_dic)
        return JsonResponse({
            'message': {
                'text': '게임이 끝났어. 게임을 종료할게. 데이터를 초기화했어'
            },
            'keyboard': {
                'type': 'text'
            }
        })
    else:
        answer = ""
        if data_dic[user_key][game_name+'_q'] != -1:
            answer = "정답 : " + '\n' + str(df.loc[data_dic[user_key][game_name+'_q'], a]) + '\n\n'

        if content.find('ㅇ') != -1:
            data_dic[user_key][game_name+'_done'].append(data_dic[user_key][game_name+'_q'])
            total_list.remove(data_dic[user_key][game_name+'_q'])
            if len(total_list) == 0:
                data_dic[user_key]['game_start'] = 0
                data_dic[user_key]['game_mode'] = '.'
                del data_dic[user_key][game_name + '_done']
                del data_dic[user_key][game_name + '_q']
                save_data(data_dic)
                return JsonResponse({
                    'message': {
                        'text': '게임이 끝났어. 게임을 종료할게. 데이터를 초기화했어'
                    },
                    'keyboard': {
                        'type': 'text'
                    }
                })

        question_ix = random.sample(total_list, 1)[0]
        data_dic[user_key][game_name+'_q'] = question_ix
        question = "문제 : " + '\n' + str(df.loc[question_ix, q])

        save_data(data_dic)
        return JsonResponse({
            'message': {
                'text': output + answer + question
            },
            'keyboard': {
                'type': 'text'
            }
        })

@csrf_exempt
def answer(request):
    global WAIT

    while WAIT:
        a = 0
    WAIT = True

    json_str = (request.body).decode('utf-8')
    received_json = json.loads(json_str)
    content = received_json['content']
    find = find_func(content) #helpful function wrapper

    user_key = received_json['user_key']
    data_dic = load_data(user_key=user_key)

    if find('초기화'):
        if user_key in data_dic.keys():
            del data_dic[user_key]
        data_dic[user_key] = {'game_start' : 0}
        data_dic[user_key]['game_mode'] = '.'
        save_data(data_dic)
        return JsonResponse({
            'message': {
                'text': '초기화했어!'
            },
            'keyboard': {
                'type': 'text'
            }
        })

    if data_dic[user_key]['game_start'] == 1:
        if data_dic[user_key]['game_mode'] == '.':
            files = os.listdir('./data')
            files = [x.split('.')[0] for x in files]
            if content in files:
                data_dic[user_key]['game_mode'] = content
                return do_game("", data_dic[user_key]['game_mode'], data_dic, user_key, reverse=False)
            else:
                save_data(data_dic)
                return JsonResponse({
                    'message': {
                        'text': '정확한 명칭을 다시 입력해줘'
                    },
                    'keyboard': {
                        'type': 'text'
                    }
                })
        else:
            return do_game(content, data_dic[user_key]['game_mode'], data_dic, user_key, reverse=False)

    if find('문제') and find('출제'):
        files = os.listdir('./data')
        files= [x.split('.')[0] for x in files]
        lts = ', '.join(files)

        resp = '출제할 문제로 [' + lts + ']가 있어! 어떤 문제를 출제해줄까?'
        data_dic[user_key]['game_start'] = 1
        save_data(data_dic)
        return JsonResponse({
            'message': {
                'text': resp
            },
            'keyboard': {
                'type': 'text'
            }
        })

    else:
        WAIT = False
        return JsonResponse({
            'message': {
                'text': '학습되지 않은 명령어야 ㅜㅜ!'
            },
            'keyboard': {
                'type': 'text'
            }
        })




