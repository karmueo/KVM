import WenZiShiBie as wz

box_tl_x = 302
box_tl_y = 188
box_br_x = 360
box_br_y = 206
bbox = [box_tl_x, box_tl_y, box_br_x, box_br_y]
sb_str = wz.wzsb('E:/testNetAPI/testNetAPI/ImgTest/process_2.jpg', bbox)
print(sb_str)

move_list = [-1,0,1]

for i in move_list:
    for j in move_list:
        box_tl_x += i
        box_br_x += i
        box_tl_y += j
        box_br_y += j
        bbox = [box_tl_x, box_tl_y, box_br_x, box_br_y]
        sb_str = wz.wzsb('E:/testNetAPI/testNetAPI/ImgTest/process_2.jpg', bbox)
        str = 'i={}, j={}, str={}'.format(i, j, sb_str)
        print(str)
