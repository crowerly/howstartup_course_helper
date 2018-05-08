import cv2
import time
from PIL import ImageGrab
import pytesseract
import pyautogui as pag
from aip import AipOcr

APP_ID = ' '
API_KEY = ' '
SECRET_KEY = ' '

client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

#答案
answer = ['需求', '考核', '不需要']
flash_start_x = 420
flash_start_y = 260
flash_end_x = 1470
flash_end_y = 1810
base_point_x = 240
base_point_y = 330
y_offset = 40
confirm_button = 4.5


def print_screen(pic_name):
    im = ImageGrab.grab()
    im.save(pic_name + '.jpeg', 'jpeg')
    return im


def img_hash(img):
    # 缩放为8*8
    img = cv2.resize(img, (8, 8), interpolation=cv2.INTER_CUBIC)
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # s为像素和初值为0，hash_str为hash值初值为''
    s = 0
    hash_str = ''
    # 遍历累加求像素和
    for i in range(8):
        for j in range(8):
            s = s + gray[i, j]
    # 求平均灰度
    avg = s / 64
    # 灰度大于平均值为1相反为0生成图片的hash值
    for i in range(8):
        for j in range(8):
            if gray[i, j] > avg:
                hash_str = hash_str + '1'
            else:
                hash_str = hash_str + '0'
    return hash_str


def hash_cmp(former_hash, latter_hash):
    hash_len = len(former_hash)
    miss = 0
    for i in range(hash_len):
        if former_hash[i] != latter_hash[i]:
            miss += 1
    return miss


def get_file_content(file_path):
    with open(file_path, 'rb') as fp:
        return fp.read()


def bd_parse(src):
    image = get_file_content(src)
    client.basicGeneral(image)
    options = {"language_type": "CHN_ENG", "detect_direction": "true", "detect_language": "true", "probability": "true"}
    e = client.basicAccurate(image, options)['words_result']
    lis = []
    for i in e:
        lis.append(i['words'])

    if '提交' in lis:
        end = lis.index('提交')
        lis = lis[end - 4:end]
    return lis


def issue_handler(img_src, local_model=True):
    if local_model:
        text = pytesseract.image_to_string(img_src, lang='chi_sim')
        parse_list = text.split("\n")
        # 处理List，删掉空的项
        for i in parse_list:
            if '' in parse_list:
                parse_list.remove('')
            if ' ' in parse_list:
                parse_list.remove(' ')
    else:
        cv2.imwrite('result.jpeg', img_src)
        parse_list = bd_parse('result.jpeg')

    count = 0
    cur_answer = ''
    for i in range(len(parse_list)):
        if answer[0] in parse_list[i]:
            count += 1
            answer.pop(0)
            cur_answer = parse_list[i]
            break

    if count == 0:
        for j in range(len(parse_list)):
            for i in range(len(answer)):
                if answer[i] in parse_list[j]:
                    answer.pop(i)
                    cur_answer = parse_list[j]
                    count += 1
                    break

            if count == 1:
                break

    # 如果匹配不成功，则答案可能为缩写，进行字符串匹配。由于规模较小，采用直接匹配
    if count == 0:
        for j in range(len(parse_list)):
            loop_flag = False
            for i in range(len(answer)):
                char_array = list(answer[i])
                for k in range(len(char_array)):
                    if char_array[k] in parse_list[j]:
                        count += 1

                        if count >= 2:
                            answer.pop(i)
                            cur_answer = parse_list[j]
                            loop_flag = True
                            break
                        else:
                            count = 0

                    if loop_flag:
                        break
            if loop_flag:
                break

    if 'A' in cur_answer:
        return 0
    elif 'B' in cur_answer:
        return 1
    elif 'C' in cur_answer:
        return 2
    elif 'D' in cur_answer:
        return 3

    multiple_choice = pag.locateOnScreen('select1.png')

    if multiple_choice != 'None':
        if local_model and ('A' in text or 'C' in text or 'C' in text or 'D' in text):
            # 如果本地库无法识别，调用百度的智能识别API
            print('type:bd')
            return issue_handler(img_src, False)
        else:
            return -3
    else:
        return -3


if __name__ == '__main__':
    time.sleep(2)
    while answer:
        former = print_screen("former")
        time.sleep(35)
        latter = print_screen("latter")

        # 二维数组切片，用于从截屏中取下flash框架
        cv2_former = cv2.imread('former.jpeg')[flash_start_x:flash_end_x, flash_start_y:flash_end_y]
        cv2_latter = cv2.imread('latter.jpeg')[flash_start_x:flash_end_x, flash_start_y:flash_end_y]

        n = hash_cmp(img_hash(cv2_former), img_hash(cv2_latter))
        if n < 10:
            ret_code = issue_handler(cv2_latter)
            print('hash_code is ' + str(n) + ' ret_code is : ' + str(ret_code))

            if ret_code != -3:
                pag.click(base_point_x, base_point_y + y_offset * ret_code)
                pag.click(base_point_x, base_point_y + y_offset * confirm_button)
                time.sleep(2)
                pag.click(base_point_x, base_point_y + y_offset * confirm_button)
                print('hit the target, the answer is ' + chr(65 + ret_code))
            else:
                print('not the target')

            print()
