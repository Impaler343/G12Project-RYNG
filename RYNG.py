from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import font
from PIL import ImageTk, Image
from idlelib.tooltip import Hovertip  # / Alt text for buttons

import mysql.connector
import datetime
import math
import secrets
import random
import threading
import time
import traceback
import pyglet  # / add fonts

# / Setting up tkinter window

root = Tk()
root.title("Main window")
root.state('zoomed')  # / fullscreen
root.iconbitmap('logo.ico')

stylerr = ttk.Style(root)  # / design and look of windows
stylerr.theme_use('clam')

ref_img = PhotoImage(file='refresh-button.png')

# / Adding fonts
pyglet.font.add_directory('.')
font_names = ['Open Sans Regular', 'Comfortaa']

# / Declaring global variables

mydb = c = None  # / mySQL server object and cursor
db_name = None  # / Currently active database (user)

main_tree = None  # / Object holding widget showing list of decks
back_btn = None
deck_name = None  # / Currently active deck (table)
recent_cards = None
alg_intensity = None  # / Mode of algorithm associated with current deck
reversal = False  # / Indicator for reverse cards while testing memory being allowed

night_mode_on = False  # / Indicator for theme mode
main_open = False  # / Indicator for main screen being active
win2_open = False  # / Indicator for add cards window being active
win3_open = False  # / Indicator for browsing cards window being active
test_open = False  # / Indicator for the memory testing screen being active
# / Indicator for the memory testing (with answers) screen being active
test2_open = False
# / Indicator for the add cards (without new deck) window being active
add_win_open = False
# / Indicator for the add cards (new deck) window being active
deck_win_open = False
radio_selection = None
front_show = None
back_show = None
notes_show = None
radios = None
done_btn = None
show_btn = None
radio_selection = None
tree_frame = None

available_cards = []
cards = []

card_index = 0
# / indicator for whether cards are available for testing or not
areCardsAvailable = False

# / Function definitions

'''
In our program, there are many instances where time objects are used, but these objects
are different than the normal datetime objects that python has.
Our objects, for the purpose of effective manipulation, are stored differently.
These so called "list-time" objects are stored as 5 element lists.
The format is as follows :
[Year,Month,Day,Hour,Minute,Second]
'''


def current_time_listobj():
    '''
    Returns a list containing current time.
    '''

    x = datetime.datetime.now()
    return [
        int(x.strftime('%Y')),
        int(x.strftime('%m')),
        int(x.strftime('%d')),
        int(x.strftime('%H')),
        int(x.strftime('%M')),
        int(x.strftime('%S'))
    ]


def deltaSet(delta):
    '''
    Adds a particular interval of time to the current time,
    and returns a list-time object.
    '''
    c_time = current_time_listobj()
    unlock_time = [0, 0, 0, 0, 0, 0]

    seconds = c_time[5]+delta[5]
    mind = 0
    if seconds >= 60:
        mind = seconds//60
        seconds = seconds % 60

    minutes = c_time[4]+delta[4]+mind
    hourd = 0
    if minutes >= 60:
        hourd = minutes//60
        minutes = minutes % 60

    hours = c_time[3]+delta[3]+hourd
    dayd = 0
    if hours > 23:
        dayd = hours//23
        hours = hours % 23

    day_month_relations = {
        1: 31, 2: 28 if c_time[0] % 4 != 0 else 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }

    days = c_time[2]+delta[2]+dayd
    monthd = 0
    if days > day_month_relations[c_time[1]]:
        i = c_time[1]
        while days > day_month_relations[i]:
            days -= day_month_relations[i]
            monthd += 1
            i += 1
        # monthd += 1
        # days = days % day_month_relations[c_time[1]]

    months = c_time[1]+delta[1]+monthd
    yeard = 0
    if months > 12:
        while months > 12:
            yeard += 1
            months -= 12

    years = c_time[0]+delta[0]+yeard

    unlock_time = [
        years, months, days, hours, minutes, seconds
    ]
    return unlock_time


def differentialFind(t1):
    '''
    Finds the difference between two given list-time objects,
    returns another list-time object.
    '''
    t2 = current_time_listobj()
    diffi = [0, 0, 0, 0, 0, 0]

    seconds = t2[5]-t1[5]
    mind = 0
    if seconds < 0:
        mind = (seconds//60)
        seconds = 60+seconds

    minutes = t2[4]-t1[4]+mind
    hourd = 0
    if minutes < 0:
        hourd = (minutes//60)
        minutes = 60+minutes

    hours = t2[3]-t1[3]+hourd
    dayd = 0
    if hours < 0:
        dayd = hours//23
        hours = 23 + hours

    day_month_relations = {
        1: 31, 2: 28 if t2[0] % 4 != 0 else 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }

    days = t2[2]-t1[2]+dayd
    monthd = 0
    if days < 0:
        i = t2[1]
        while days < 0:
            monthd -= 1
            days += day_month_relations[i]
            i -= 1
            if i == 0:
                i = 12

    months = t2[1]-t1[1]+monthd
    yeard = 0
    if months < 0:
        while months < 0:
            yeard -= 1
            months += 12

    years = t2[0]-t1[0]+yeard

    diffi = [
        years, months, days, hours, minutes, seconds
    ]
    return diffi


def submit():
    '''
    Takes data from user and tries to connect to mySQL database.
    '''
    global mydb, c, sql_pass_in, eu, db_name, main_open, night_mode_on, ref_btn, ref_img
    if eu.get() and sql_pass_in.get():
        try:
            mydb = mysql.connector.connect(
                host='localhost', user='root', passwd=sql_pass_in.get())
            c = mydb.cursor(buffered=True)

            try:
                c.execute(f"create database ryng_{eu.get()}")
                c.execute(f"use ryng_{eu.get()}")
                c.execute("create table data(theme char(10))")
                c.execute(f"insert into data values('light')")
                c.execute(
                    "create table decks(name varchar(100),alg char(5),reverse char(4))")
                db_name = f'ryng_{eu.get()}'
                clear_frame(frame)
                main_open = True
                create_menu()
                create_tree(frame)
                ref_btn = Button(root, image=ref_img,
                                 command=refresh, borderwidth=0)
                ref_btn.place(relx=0.965, rely=0.02)
                frame.config(pady=100)
            except:
                c.execute(f"use ryng_{eu.get()}")
                c.execute(f"select * from data")
                db_name = f'ryng_{eu.get()}'
                x = []
                for i in c:
                    x.append(i)
                night_mode_on = True if x[0][0] == 'dark' else False
                frame.config(pady=100)
                clear_frame(frame)
                main_open = True
                create_menu()
                ref_btn = Button(root, image=ref_img,
                                 command=refresh, borderwidth=0)
                ref_btn.place(relx=0.965, rely=0.02)
                Hovertip(ref_btn, 'Refresh')
                create_tree(frame)
                if night_mode_on:
                    switch_to_night()
        except:
            messagebox.showerror("Unable to connect to mySQL!",
                                 'Make sure password is correct and server is local.')


def fixed_map(option):
    '''
    Fix for setting text colour for Tkinter 8.6.9
    Returns the style map for 'option' with any styles starting with
    ('!disabled', '!selected', ...) filtered out.
    style.map() returns an empty list for missing options, so this should be future-safe.
    '''
    # / Removing unnecessary attributes from treeview functions
    return [elm for elm in stylish.map('Treeview', query_opt=option) if
            elm[:2] != ('!disabled', '!selected')]


def create_tree(given_frame):
    '''
    Creates the interactive list of decks that is seen in the main screen.
    '''
    global stylish, main_tree, test_btn, testall_btn
    main_tree_frame = Frame(given_frame)
    main_tree_frame.pack()

    tree_scroll = Scrollbar(main_tree_frame)
    tree_scroll.pack(side=RIGHT, fill=Y)

    stylish = ttk.Style()
    stylish.configure("mine.Treeview.Heading",
                      font=(font_names[1], 13, 'bold'))
    stylish.configure('Treeview', rowheight=23, font=(font_names[1], 11))
    stylish.map('Treeview', foreground=fixed_map('foreground'),background=fixed_map('background'))
    stylish.map('Treeview', background=[('selected', '#f6738c')])

    main_tree = ttk.Treeview(main_tree_frame, height=15,
                             yscrollcommand=tree_scroll.set, style='mine.Treeview')
    main_tree['columns'] = ('Decks', 'Due', 'New')
    main_tree.column('#0', width=0, stretch=NO)
    main_tree.column('Decks', anchor=CENTER, width=250)
    main_tree.column('Due', anchor=CENTER, width=100)
    main_tree.column('New', anchor=CENTER, width=100)

    main_tree.heading('#0', text='', anchor=CENTER)
    main_tree.heading('Decks', text='Decks', anchor=CENTER)
    main_tree.heading('Due', text='Due', anchor=CENTER)
    main_tree.heading('New', text='New', anchor=CENTER)
    main_tree.pack()

    main_tree.bind('<Button-3>', deck_options)  # / button 3 for right click

    # / related scroll in y direction
    tree_scroll.config(command=main_tree.yview)

    c.execute("SELECT COUNT(*) from decks")
    x = ''
    for i in c:
        x = i
    if x:
        update_decks()

        count = 0
        for deck in deck_lst_withCardInfo:
            main_tree.insert(parent='', index='end', iid=count, tags='none',
                             text='', values=(deck[0], deck[1], deck[2]))
            count += 1

    testall_btn = Button(given_frame, text='Test all Cards', font=(font_names[0], 10),
                         command=unlockAndTestAll)
    testall_btn.pack(padx=1, pady=2)

    test_btn = Button(given_frame, text='Test', font=(font_names[0], 10),
                      command=create_test)
    test_btn.pack(padx=1, pady=2)
    if night_mode_on:
        test_btn.config(bg='#bb8bfc', fg='black')
        testall_btn.config(bg='#bb8bfc', fg='black')


def deck_options(event):
    global d_name, id
    id = main_tree.identify_row(event.y)
    if id:
        deck_menu = Menu(root, tearoff=0)
        deck_menu.add_command(
            label='Rename', command=rename_deck, activebackground='#f6738c')
        deck_menu.add_command(
            label='Delete', command=delete_deck, activebackground='#f6738c')
        main_tree.selection_set(id)
        deck_menu.post(event.x_root, event.y_root)
        deck_info = main_tree.set(id)
        d_name = deck_info['Decks']


def delete_deck():
    global d_name, win3_open
    conf = messagebox.askyesno(
        "Deck Deletion", f"Are you sure you want to delete {d_name}?")
    if conf:
        c.execute(f"delete from decks where name = '{d_name}'")
        c.execute(f"drop table deck_{d_name}")
        clear_frame(frame)
        create_tree(frame)
        if win3_open:
            clear_frame(left_frame)
            create_lframe()


def rename_deck():
    global d_name, id, edit_entry
    edit_entry = Entry(root, width=40, justify=CENTER, borderwidth=1, border=1)
    edit_entry.place(relx=0.33, rely=0.0296*(int(id)+7))
    edit_entry.focus_set()
    edit_entry.config(highlightthickness=2, highlightbackground='black')
    root.bind('<Return>', edit_deck_name)
    root.bind('<Escape>', lambda e: edit_entry.destroy())


def edit_deck_name(event):
    global d_name, edit_entry
    new = edit_entry.get()
    edit_entry.destroy()
    if new == '':
        messagebox.showerror("Empty deck name!", 'Deck cannot be nameless.')
    else:
        try:
            c.execute(
                f"update decks set name = '{new}' where name = '{d_name}'")
            c.execute(f"rename table deck_{d_name} to deck_{new}")
        except mysql.connector.Error:
            pass
        clear_frame(frame)
        create_tree(frame)
        if win3_open:
            clear_frame(left_frame)
            create_lframe()
            update_cards(decks_list.get())


def list_multiply(lst, multiplier):
    '''
    Multiplies each element in the list by a given value.
    '''
    temp = []
    for i in lst:
        temp.append(i*multiplier)
    return temp


def timeIntervalAdjust(inter):
    '''
    While multiplying a time value,
    a situation with invalid values might be reached.
    Example:
    [YYYY,MM,DD,05,00,00]*5=[YYYY,MM,DD,25,00,00]
    hour count cannot be more than or equal to 23,
    hence this function edits it.
    '''
    seconds = inter[5]
    mind = 0
    if seconds >= 60:
        mind = seconds//60
        seconds = seconds % 60
    minutes = inter[4]+mind
    hourd = 0
    if minutes >= 60:
        hourd = minutes//60
        minutes = minutes % 60
    hours = inter[3]+hourd
    dayd = 0
    if hours >= 23:
        dayd = hours//23
        hours = hours % 23
    days = inter[2]+dayd
    inter = [
        inter[0], inter[1], days, hours, minutes, seconds
    ]
    return inter


def done_func():
    '''
    Sets the new interval for cards based on user feedback and stored data.
    '''
    global available_cards, radio_selection, card_index, test2_open, back_btn
    test2_open = False

    feed = radio_selection.get()
    s = f'{feed}'
    if s != 'None' or not s:
        inter = available_cards[card_index][6]

        if alg_intensity == 'less':
            if feed == 'easy':
                inter = list_multiply(inter, 3)
            elif feed == 'good':
                inter = list_multiply(inter, 2)
            elif feed == 'hard':
                inter = list_multiply(inter, 1)
            elif feed == 'vhard':
                temp = []
                for i in inter:
                    temp.append(i // 2)
                inter = temp
            elif feed == 'forgot':
                inter = [0, 0, 0, 0, 0, 0]

            inter = timeIntervalAdjust(inter)
            # print(inter)
            inter_tosend = [0, 0, 0, 0, 5, 0] if inter == [0]*6 else inter
            # print(inter_tosend)

            unlock_time = deltaSet(inter)
            #print(f'Unlock time: {unlock_time}')
            #print(f'Lock time: {current_time_listobj()}')
            h = 'deck_' + f"{deck_name}"
            if available_cards[card_index][4] == 'New':
                c.execute(
                    f"update {h} set unlock_time='{unlock_time}',card_state = 'Learning',last_interval='{inter_tosend}',lock_time='{current_time_listobj()}' where uk_id ='{available_cards[card_index][9]}'")
            else:
                c.execute(
                    f"update {h} set unlock_time='{unlock_time}',last_interval='{inter_tosend}',lock_time='{current_time_listobj()}' where uk_id ='{available_cards[card_index][9]}'")
            mydb.commit()
            card_index += 1
            if card_index < len(available_cards):
                clear_frame(frame)
                newFrameCreate()
            else:
                back_func()
        elif alg_intensity == 'more':
            inter = available_cards[card_index][6]
            lock_time = available_cards[card_index][7]
            diff = differentialFind(lock_time)
            stage = 0
            '''
            stage values and their meaning (in terms of time diff. between locking and viewing currently):
            0 -> less than 5 mins
            1 -> btw 5 mins and 1 hour
            2 -> btw 1 hr and 1 day
            3 -> btw 1 day and 2 days
            4 -> btw 2 days and 7 days
            5 -> more than 7 days
            '''
            # checking what stage we are at
            if diff[2] > 7:
                stage = 5
            elif diff[2] >= 2 and diff[2] <= 7:
                stage = 4
            elif 1 <= diff[2] < 2:
                stage = 3
            elif diff[2] < 1 and diff[3] > 1:
                stage = 2
            elif diff[3] <= 1 and diff[4] >= 5:
                stage = 1
            elif diff[4] < 5:
                stage = 0
            #print(f'Stage: {stage},Diff: {diff}')
            #print(f'Former interval: {inter}')

            # actual stuff
            if stage > 2:
                inter = inter if inter >= diff else diff
            if stage == 0:
                if feed == 'easy':
                    inter = list_multiply(inter, 3)
                elif feed == 'good':
                    inter = list_multiply(inter, 2)
                elif feed == 'hard':
                    inter = list_multiply(inter, 1)
                elif feed == 'vhard':
                    temp = []
                    for i in inter:
                        temp.append(i // 2)
                    inter = temp
                elif feed == 'forgot':
                    inter = [0, 0, 0, 0, 0, 0]
            elif stage == 1:
                if feed == 'easy':
                    inter = [0, 0, 1, 0, 0, 0]
                elif feed == 'good':
                    inter = list_multiply(inter, 2)
                elif feed == 'hard':
                    inter = list_multiply(inter, 1)
                elif feed == 'vhard':
                    temp = []
                    for i in inter:
                        temp.append(i // 2)
                    inter = temp
                elif feed == 'forgot':
                    inter = [0, 0, 0, 0, 0, 0]
            elif stage == 2:
                if feed == 'easy':
                    inter = timeIntervalAdjust(list_multiply(inter, 2))
                elif feed == 'good':
                    inter = timeIntervalAdjust(list_multiply(inter, 2))
                elif feed == 'hard':
                    inter = [0, 0, 0, 0, 5, 0]
                elif feed == 'vhard':
                    temp = []
                    for i in inter:
                        temp.append(i // 2)
                    inter = temp
                elif feed == 'forgot':
                    inter = [0, 0, 0, 0, 0, 0]
            elif stage == 3:
                if feed == 'easy':
                    temp = []
                    for i in inter:
                        temp.append(math.floor(i*2.5))
                    inter = timeIntervalAdjust(temp)
                elif feed == 'good':
                    inter = timeIntervalAdjust(list_multiply(inter, 2))
                elif feed == 'hard':
                    inter = [0, 0, 0, 1, 0, 0]
                elif feed == 'vhard':
                    inter = [0, 0, 0, 0, 30, 0]
                elif feed == 'forgot':
                    inter = [0, 0, 0, 0, 0, 0]
            elif stage == 4:
                if feed == 'easy':
                    inter = timeIntervalAdjust(list_multiply(inter, 3))
                elif feed == 'good':
                    inter = timeIntervalAdjust(list_multiply(inter, 2))
                elif feed == 'hard':
                    inter = timeIntervalAdjust(list_multiply(inter, 1))
                elif feed == 'vhard':
                    inter = [0, 0, 0, 1, 0, 0]
                elif feed == 'forgot':
                    inter = [0, 0, 0, 0, 0, 0]
            elif stage == 5:
                if feed == 'easy':
                    inter = timeIntervalAdjust(list_multiply(inter, 4))
                elif feed == 'good':
                    inter = timeIntervalAdjust(list_multiply(inter, 3))
                elif feed == 'hard':
                    inter = timeIntervalAdjust(list_multiply(inter, 2))
                elif feed == 'vhard':
                    inter = [0, 0, 1, 0, 0, 0]
                elif feed == 'forgot':
                    inter = [0, 0, 0, 0, 0, 0]

            inter = timeIntervalAdjust(inter)
            # print(inter)
            inter_tosend = [0, 0, 0, 0, 5, 0] if inter == [0]*6 else inter
            # print(inter_tosend)
            #print(f'New interval: {inter_tosend}')

            unlock_time = deltaSet(inter)
            #print(f'Unlock time: {unlock_time}')
            #print(f'Lock time: {current_time_listobj()}')
            #print(f'Deck name: {deck_name}')
            #print(f'Card ID: {available_cards[card_index][9]}')
            h = 'deck_' + f"{deck_name}"
            if available_cards[card_index][4] == "New":
                if available_cards[card_index][8]:
                    c.execute(
                        f"update {h} set unlock_time='{unlock_time}',card_state = 'Learning',last_interval='{inter_tosend}',lock_time='{current_time_listobj()}' where uk_id ='{available_cards[card_index][9]}'")
                else:
                    c.execute(
                        f"update {h} set unlock_time='{unlock_time}',card_state = 'Learning',last_interval='{inter_tosend}',lock_time='{current_time_listobj()}' where uk_id ='{available_cards[card_index][9]}'")
            else:
                if available_cards[card_index][8]:
                    c.execute(
                        f"update {h} set unlock_time='{unlock_time}',last_interval='{inter_tosend}',lock_time='{current_time_listobj()}' where uk_id ='{available_cards[card_index][9]}'")
                else:
                    c.execute(
                        f"update {h} set unlock_time='{unlock_time}',last_interval='{inter_tosend}',lock_time='{current_time_listobj()}' where uk_id ='{available_cards[card_index][9]}'")
            mydb.commit()
            card_index += 1
            if card_index < len(available_cards):
                clear_frame(frame)
                newFrameCreate()
                #print('Tried to fetch next card.')
            else:
                back_func()
                #print('Jumped back to main screen.')

    else:
        messagebox.showerror("No selection!", 'Chooose an option')
    # print('\n\n')


def show_func():
    '''
    To show the other side and notes of a card on user demand
    '''
    global done_btn, radio_selection, test2_open, test_open, b, n, radios_frame, spa1, spa2, spa3, spa4, ea_radio, go_radio, ha_radio, vh_radio, fo_radio, ch_pic, ne_pic, ch_label

    test2_open = True
    test_open = False

    ch_pic = PhotoImage(file='checkmark.png')
    ch_label = Label(frame, image=ch_pic)
    ch_label.place(relx=0.48, rely=0.74)

    ne_pic = PhotoImage(file='next.png')

    radios_frame = Frame(frame)
    radios_frame.place(relx=0.34, rely=0.85)

    radio_selection = StringVar()

    b = f'Back: {available_cards[card_index][1]}' if available_cards[card_index][1] != '' else ''
    n = f'Notes: {available_cards[card_index][2]}' if available_cards[card_index][2] != '' else ''

    ea_radio = Radiobutton(radios_frame, text='Easy', takefocus=0, font=(font_names[1], 11),
                           variable=radio_selection, value='easy')
    ea_radio.grid(row=0, column=0)

    spa1 = Label(radios_frame, text='     ')
    spa1.grid(row=0, column=1)

    go_radio = Radiobutton(radios_frame, text='Good', takefocus=0, font=(font_names[1], 11),
                           variable=radio_selection, value='good')
    go_radio.grid(row=0, column=2)

    spa2 = Label(radios_frame, text='     ')
    spa2.grid(row=0, column=3)

    ha_radio = Radiobutton(radios_frame, text='Hard', takefocus=0, font=(font_names[1], 11),
                           variable=radio_selection, value='hard')
    ha_radio.grid(row=0, column=4)

    spa3 = Label(radios_frame, text='     ')
    spa3.grid(row=0, column=5)

    vh_radio = Radiobutton(radios_frame, text='Very hard', takefocus=0, font=(font_names[1], 11),
                           variable=radio_selection, value='vhard')
    vh_radio.grid(row=0, column=6)

    spa4 = Label(radios_frame, text='     ')
    spa4.grid(row=0, column=7)

    fo_radio = Radiobutton(radios_frame, text='Forgot', takefocus=0, font=(font_names[1], 11),
                           variable=radio_selection, value='forgot')
    fo_radio.grid(row=0, column=8)
    radio_selection.set(None)

    if night_mode_on:
        radios_frame.config(bg='#121212')
        spa1.config(bg='#121212')
        spa2.config(bg='#121212')
        spa3.config(bg='#121212')
        spa4.config(bg='#121212')
        show_btn.config(image=ne_pic, command=done_func, borderwidth=0,
                        bg='#121212')
        Hovertip(show_btn, 'Next')
        ch_label.config(bg='#121212')
        show_btn.place_configure(relx=0.485)
        back_show.configure(text=b, bg='#121212', fg='#a87ae0')
        notes_show.configure(text=n, bg='#121212', fg='#a87ae0')
        fo_radio.config(bg='#2e2e2e', fg='white',
                        selectcolor='#6213a8', activebackground='#121212')
        vh_radio.config(bg='#2e2e2e', fg='white',
                        selectcolor='#6213a8', activebackground='#121212')
        ha_radio.config(bg='#2e2e2e', fg='white',
                        selectcolor='#6213a8', activebackground='#121212')
        go_radio.config(bg='#2e2e2e', fg='white',
                        selectcolor='#6213a8', activebackground='#121212')
        ea_radio.config(bg='#2e2e2e', fg='white',
                        selectcolor='#6213a8', activebackground='#121212')
    else:
        back_show.configure(text=b)
        notes_show.configure(text=n)
        show_btn.place_configure(relx=0.485)
        Hovertip(show_btn, 'Next')
        show_btn.config(image=ne_pic, command=done_func, borderwidth=0)


def create_stree():
    global search_tree
    tree_scroll = Scrollbar(tree_frame)
    tree_scroll.pack(side=RIGHT, fill=Y)

    search_tree = ttk.Treeview(
        tree_frame, yscrollcommand=tree_scroll.set, style='mine.Treeview', height=15)
    # f6738c
    # f6738c
    search_tree['columns'] = ('Front', 'Back', 'uk_id')
    search_tree.column('#0', width=0, stretch=NO)
    search_tree.column('Front', anchor=CENTER, width=400)
    search_tree.column('Back', anchor=CENTER, width=400)
    search_tree.column('uk_id', width=0, stretch=NO)

    search_tree.heading('#0', text='', anchor=CENTER)
    search_tree.heading('Front', text='Front', anchor=CENTER)
    search_tree.heading('Back', text='Back', anchor=CENTER)
    search_tree.heading('uk_id', text='', anchor=CENTER)

    search_tree.bind("<ButtonRelease-1>", fill_boxes)

    search_tree.pack(fill='both', expand=True)

    tree_scroll.config(command=search_tree.yview)


def back_func():
    '''
    Resets UI to go back to main screen.
    '''
    global test2_open, test_open, main_open, ref_btn, ref_img
    test_open = False
    test2_open = False
    main_open = True
    clear_frame(frame)
    ref_btn = Button(root, image=ref_img, command=refresh, borderwidth=0)
    ref_btn.place(relx=0.965, rely=0.02)
    create_menu()
    create_tree(frame)
    frame.config(pady=100)
    if night_mode_on:
        ref_btn.config(bg='#121212', activebackground='#121212')


def refresh():
    global tree_frame, win3_open, ref_img, night_mode_on, ref_btn
    clear_frame(frame)
    create_tree(frame)
    ref_btn = Button(root, image=ref_img, command=refresh, borderwidth=0)
    if night_mode_on:
        ref_btn.config(bg='#121212', activebackground='#121212')
    ref_btn.place(relx=0.965, rely=0.02)
    if win3_open:
        clear_frame(tree_frame)
        create_stree()


def newFrameCreate():
    '''
    Creates frame for memory testing.
    '''
    global front_show, show_btn, back_show, notes_show, test_open, main_open, back_btn, frame, label_space, back_img, show_picl, show_picd1
    test_open = True
    main_open = False
    ref_btn.destroy()
    frame.config(pady=50)
    back_img = PhotoImage(file='back.png')
    back_btn = Button(frame, command=back_func, image=back_img, borderwidth=0)
    back_btn.pack()
    Hovertip(back_btn, 'Back To Home')

    label_space = Label(frame, text='')
    label_space.pack(pady=10)

    front_show = Label(
        frame, text=f'Front: {available_cards[card_index][0]}', font=(font_names[1], 16))
    front_show.pack(pady=10)

    back_show = Label(frame, text='', font=(font_names[1], 14), takefocus=1)
    back_show.pack(pady=5)

    notes_show = Label(frame, text='', font=(font_names[1], 11))
    notes_show.pack(pady=10)

    show_picl = PhotoImage(file='cardsl.png')
    show_picd1 = PhotoImage(file='cardsd1.png')

    show_btn = Button(frame, image=show_picl, borderwidth=0,
                      command=show_func)
    show_btn.place(relx=0.48, rely=0.95)
    Hovertip(show_btn, 'Show')

    if night_mode_on:
        front_show.config(bg='#121212', fg='#a87ae0')
        show_btn.config(bg='#121212', image=show_picd1,
                        activebackground='#121212')
        back_btn.config(bg='#121212', activebackground='#121212')
        back_show.config(bg='#121212')
        notes_show.config(bg='#121212')
        label_space.config(bg='#121212')


def create_test():
    '''
    Fetches card data from selected deck in order to test memory.
    '''
    global available_cards, deck_name, card_index, alg_intensity, reversal
    if main_tree.selection():
        deck_iid = main_tree.selection()[0]
        deck_info = main_tree.set(deck_iid)
        deck_name = deck_info['Decks']
        c.execute(f"select alg,reverse from decks where name='{deck_name}'")
        # will only run once, loop is only to avoid error
        for i in c:
            alg_intensity = str(i[0]).strip()
            if str(i[1]).strip() == 'yes':
                reversal = True
            else:
                reversal = False
        h = 'deck_' + f"{deck_name}"
        due = 0
        c.execute(f"select unlock_time,last_interval from {h}")
        t1 = datetime.datetime.now()
        for j in c:
            t = eval(f'{j[0]}')
            t2 = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])
            if t1 > t2:
                due += 1
        if due > 0:
            h = 'deck_' + f"{deck_name}"
            c.execute(f'select * from {h}')
            card_index = 0
            available_cards = []
            t1 = datetime.datetime.now()
            if reversal:
                for i in c:
                    t = eval(f'{i[5]}')
                    t2 = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])
                    t = eval(f'{i[7]}')
                    t3 = [t[0], t[1], t[2], t[3], t[4], t[5]]
                    if t1 > t2:
                        if random.randint(0, 1) == 1:
                            available_cards.append([
                                i[0], i[1], i[2], i[3], i[4], t2, eval(
                                    f'{i[6]}'), t3, True, i[8]
                            ])
                        else:
                            available_cards.append([
                                i[1], i[0], i[2], i[3], i[4], t2, eval(
                                    f'{i[6]}'), t3, False, i[8]
                            ])
                        clear_frame(frame)
                        newFrameCreate()
            else:
                for i in c:
                    t = eval(f'{i[5]}')
                    t2 = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])
                    t = eval(f'{i[7]}')
                    t3 = [t[0], t[1], t[2], t[3], t[4], t[5]]
                    if t1 > t2:
                        available_cards.append([
                            i[0], i[1], i[2], i[3], i[4], t2, eval(
                                f'{i[6]}'), t3, False, i[8]
                        ])
                        clear_frame(frame)
                        newFrameCreate()
        else:
            messagebox.showinfo(
                "No cards due!", 'You have learnt this deck for now')
    else:
        messagebox.showerror("No Deck Selected!",
                             'Select a deck first')


def unlockAndTestAll():
    '''
    Unlocks all cards and launches test for them (for when user may want to test all together).
    '''
    global available_cards, deck_name, card_index, alg_intensity, reversal
    if main_tree.selection():
        deck_iid = main_tree.selection()[0]
        deck_info = main_tree.set(deck_iid)
        deck_name = deck_info['Decks']
        current_time = current_time_listobj()
        c.execute(f"update deck_{deck_name} set unlock_time='{current_time}'")
        c.execute(
            f"select unlock_time,last_interval,lock_time,uk_id from deck_{deck_name}")
        x = []
        for i in c:
            x += (i,)
        cards = x
        conf = messagebox.askyesno(
            f"There are {len(cards)} cards in this deck", "Do you want to learn all of them?")
        if conf:
            cards_lst = []
            for card in cards:
                last_interval = eval(f'{card[1]}')
                lock_time = eval(f'{card[2]}')
                diffi = differentialFind(lock_time)
                if diffi >= last_interval:
                    cards_lst.append(list(card))
                elif diffi < last_interval:
                    temp = []
                    if diffi[2] != 0:
                        if last_interval[2]/diffi[2] >= 4:
                            for i in last_interval:
                                temp.append(i//4)
                        elif last_interval[2]/diffi[2] >= 3:
                            for i in last_interval:
                                temp.append(i//3)
                        elif last_interval[2]/diffi[2] >= 2:
                            for i in last_interval:
                                temp.append(i//2)
                        else:
                            temp = diffi
                    else:
                        if last_interval[2] != 0:
                            if last_interval[2] * 24 - diffi[3] > 20:
                                for i in last_interval:
                                    temp.append(i//3)
                            else:
                                temp = diffi
                        else:
                            if diffi[3] != 0 and last_interval[3]/diffi[3] >= 4:
                                for i in last_interval:
                                    temp.append(i//4)
                            elif diffi[3] != 0 and last_interval[3]/diffi[3] >= 2:
                                for i in last_interval:
                                    temp.append(i//2)
                            else:
                                temp = diffi

                    cards_lst.append(
                        [card[0], f'{temp}', card[2], card[3]])
            for card in cards_lst:
                c.execute(
                    f"update deck_{deck_name} set unlock_time='{card[0]}',last_interval='{card[1]}',lock_time='{card[2]}' where uk_id='card[3]'")
            mydb.commit()
            update_decks()
            create_test()

    else:
        messagebox.showerror("No Deck Selected!",
                             'Select a deck first')


def askconf():
    '''
    Confirms logout from user and switches to login view.
    '''
    global win3_open, win2_open, frame, main_open, night_mode_on, stylish, main_menu, db_name
    conf = messagebox.askyesno(
        "Logout Confirmation", "Are you sure you want to logout?")
    if conf:
        if win2_open:
            win2.destroy()
        if win3_open:
            win3.destroy()
        main_menu.destroy()
        clear_frame(options_frame)
        ref_btn.destroy()
        options_frame.config(bg='#f0f0f0')
        frame.destroy()
        stylish.configure("Treeview", background='white',
                          foreground='black', fieldbackground='white')
        root.config(bg='#f0f0f0')
        create_main_screen()
        db_name = None


def create_main_screen():
    '''
    Collects login credentials from the user.
    Three things are collected:
    1. mySQL password
    2. Username
    '''
    global frame, sql_pass_in, logo_img, eu
    frame = Frame(root)
    frame.pack(pady=10, fill='both', expand=True)

    logo_img = PhotoImage(file='logo.png')
    logo_label_light = Label(frame, image=logo_img)
    logo_label_light.pack(pady=20)

    sql_pass = Label(frame, text='mySQL password:',
                     font=(font_names[1], 18))
    sql_pass.pack(ipady=8)

    sql_pass_in = Entry(frame, width=50, borderwidth=0, bg='#f4d595',
                        justify='center', font=(font_names[1], 18))
    sql_pass_in.config(show='*')
    sql_pass_in.pack(ipady=10)

    us = Label(frame, text='Username:', font=(font_names[1], 18))
    us.pack(ipady=10)

    eu = Entry(frame, width=50, borderwidth=0, bg='#f4d595',
               justify='center', font=(font_names[1], 18))
    eu.pack(ipady=10)

    subbtn = Button(frame, text='Submit', command=submit, borderwidth=1,
                    font=(font_names[0], 15))
    subbtn.pack(pady=10)
    root.bind('<Return>', lambda event=None: subbtn.invoke())


def clear_frame(frame_name):
    '''
    Clears all the widgets inside a given frame.
    '''
    for widget in frame_name.winfo_children():
        widget.destroy()


def update_decks():
    '''
    Fetches data from database and updates onscreen display for the same.
    '''
    global deck_lst, deck_lst_withCardInfo, areCardsAvailable
    # print('Updating decks...')
    mydb.commit()
    c.execute("select name from decks")
    dues = []
    deck_lst = []
    deck_lst_withCardInfo = []
    for i in c:
        deck_lst.append(i)

    for i in deck_lst:
        h = 'deck_' + f"{i[0]}"
        due = 0
        new = 0
        c.execute(f"select unlock_time,last_interval,card_state from {h}")
        t1 = datetime.datetime.now()
        for j in c:
            t = eval(f'{j[0]}')
            t2 = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])
            if t1 > t2:
                due += 1
            if j[2] == 'New':
                new += 1

        #print(h, due)

        deck_lst_withCardInfo.append([i[0], due, new])
        dues.append(due)

    for due in dues:
        if due > 0:
            areCardsAvailable = True
    if dues.count(0) == len(dues):
        areCardsAvailable = False


def create_menu():
    '''
    Creates the options seen in the top left menu and links them to respective functions.
    '''
    global options_frame, addc_btn, br_btn, the_btn, options_menu, main_menu, d_img, l_img, add_img, br_img, delacc, clr_pic, log_pic

    delacc = PhotoImage(file='delacc.png')
    clr_pic = PhotoImage(file='cleardata.png')
    log_pic = PhotoImage(file='logoutacc.png')

    main_menu = Menu(root)
    root.config(menu=main_menu)
    options_menu = Menu(main_menu, tearoff=False)
    main_menu.add_cascade(
        label="Options", menu=options_menu)
    options_menu.add_command(command=clearAccount,
                             image=clr_pic, activebackground='#f6738c')
    options_menu.add_command(
        command=askconf, image=log_pic, activebackground='#f6738c')
    options_menu.add_command(
        command=clearData, image=delacc, activebackground='#f6738c')

    options_frame = Frame(root)
    options_frame.place(relx=0.445, rely=0)

    add_img = PhotoImage(file='plus.png')
    addc_btn = Button(options_frame, image=add_img,
                      borderwidth=0, command=add_dem_cards)
    addc_btn.pack(side=LEFT, pady=5)
    Hovertip(addc_btn, 'Add Decks/Cards')

    br_img = PhotoImage(file='browse.png')
    br_btn = Button(options_frame, image=br_img,
                    borderwidth=0, command=browse_cards)
    br_btn.pack(side=LEFT, pady=5, padx=20)
    Hovertip(br_btn, 'Browse/Edit Cards')

    d_img = PhotoImage(file='nighttheme.png')
    l_img = PhotoImage(file='lighttheme.png')
    the_btn = Button(options_frame, image=d_img,
                     command=switch_to_night, borderwidth=0)
    the_btn.pack(side=LEFT, pady=5)
    Hovertip(the_btn, 'Switch Theme')

    if night_mode_on:
        options_frame.config(bg='#121212')
        addc_btn.config(bg='#121212', activebackground='#121212')
        br_btn.config(bg='#121212', activebackground='#121212')
        the_btn.config(bg='#121212', command=switch_to_day,
                       activebackground='#121212', image=l_img)


def switch_to_night():
    '''
    Changes element and font colours to dark theme specifics.
    '''
    global night_mode_on
    night_mode_on = True
    root.config(bg='#121212')
    frame.config(bg='#121212')
    options_frame.config(bg='#121212')
    addc_btn.config(bg='#121212', activebackground='#121212')
    br_btn.config(bg='#121212', activebackground='#121212')
    the_btn.config(bg='#121212', command=switch_to_day,
                   activebackground='#121212', image=l_img)
    if main_open:
        test_btn.config(bg='#bb8bfc', fg='black')  # test btn
        testall_btn.config(bg='#bb8bfc', fg='black')
        ref_btn.config(bg='#121212', activebackground='#121212')
    if win2_open:
        frame2.config(bg='#121212')
        drop.config(bg='#121212', fg='white')
    if win3_open:
        win3.config(bg='#121212')
        left_frame.config(bg='#121212')
        right_frame.config(bg='#121212')
        red_radio.config(bg='#da383e', activebackground='#da383e')
        or_radio.config(bg='#f08e32', activebackground='#f08e32')
        bl_radio.config(bg='#36a1eb', activebackground='#36a1eb')
        gr_radio.config(bg='#32ae8a', activebackground='#32ae8a')
        no_radio.config(bg='#2e2e2e', activebackground='#2e2e2e')
        front_edit.config(bg='#ababab')
        back_edit.config(bg='#ababab')
        notes_edit.config(bg='#ababab')
        search_entry.config(bg='#ababab')
        boxes_frame.config(bg='#121212')
        ed_del_frame.config(bg='#121212')
        flag_frame.config(bg='#121212')
        win3.config(bg='#121212')
        sp1.config(bg='#121212')
        sp2.config(bg='#121212')
        sp3.config(bg='#121212')
        sp4.config(bg='#121212')
        spacee_label.config(bg='#121212')
        s_label.config(bg='#121212', image=sd_img)
        flag_radio.config(bg='#121212', fg='#a87ae0')
        dupl_btn.config(bg='#bb8bfc', fg='black')
        edit_btn.config(bg='#121212', image=edd_img)
        delete_btn.config(bg='#121212')

    if test_open:
        front_show.config(bg='#121212', fg='#a87ae0')
        show_btn.config(bg='#121212', image=show_picd1,
                        activebackground='#121212')
        back_show.config(bg='#121212')
        notes_show.config(bg='#121212')
        back_btn.config(bg='#121212', activebackground='#121212')
        label_space.config(bg='#121212')
    if deck_win_open:
        rev_lb.config(bg='#121212')
        alg_lb.config(bg='#121212')
        deck_label.config(bg='#121212', fg='#a87ae0')
        abtn.config(bg='#bb8bfc', fg='black')
        deck_entry.config(bg='#ababab')
        yes_btn.config(bg='#121212', fg='white',
                       selectcolor='#6213a8', activebackground='#121212')
        no_btn.config(bg='#121212', fg='white',
                      selectcolor='#6213a8', activebackground='#121212')
        more_btn.config(bg='#121212', fg='white',
                        selectcolor='#6213a8', activebackground='#121212')
        less_btn.config(bg='#121212', fg='white',
                        selectcolor='#6213a8', activebackground='#121212')
    if add_win_open:
        b_label.config(bg='#121212', fg='#a87ae0')
        f_label.config(bg='#121212', fg='#a87ae0')
        n_label.config(bg='#121212', fg='#a87ae0')
        add_btn.config(bg='#bb8bfc', fg='#a87ae0')
        entry_front.config(bg='#ababab')
        entry_back.config(bg='#ababab')
        entry_notes.config(bg='#ababab')
    if test2_open:
        radios_frame.config(bg='#121212')
        fo_radio.config(bg='#2e2e2e', fg='white',
                        selectcolor='#6213a8', activebackground='#121212')
        vh_radio.config(bg='#2e2e2e', fg='white',
                        selectcolor='#6213a8', activebackground='#121212')
        ha_radio.config(bg='#2e2e2e', fg='white',
                        selectcolor='#6213a8', activebackground='#121212')
        go_radio.config(bg='#2e2e2e', fg='white',
                        selectcolor='#6213a8', activebackground='#121212')
        ea_radio.config(bg='#2e2e2e', fg='white',
                        selectcolor='#6213a8', activebackground='#121212')
        ch_label.config(bg='#121212')
        back_btn.config(bg='#121212')
        label_space.config(bg='#121212')
        spa1.config(bg='#121212')
        spa2.config(bg='#121212')
        spa3.config(bg='#121212')
        spa4.config(bg='#121212')
        show_btn.config(image=ne_pic, command=done_func, borderwidth=0, activebackground='#121212',
                        bg='#121212')
        front_show.config(bg='#121212', fg='#a87ae0')
        back_show.config(text=b, bg='#121212', fg='#a87ae0')
        notes_show.config(text=n, bg='#121212', fg='#a87ae0')
    stylish.configure("Treeview", background='#2e2e2e',
                      foreground='white', fieldbackground='#2e2e2e')
    c.execute("update data set theme='dark'")
    mydb.commit()


def switch_to_day():
    '''
    Changes element and font colours to light theme specifics.
    '''
    global night_mode_on
    night_mode_on = False
    root.config(bg='#f0f0f0')
    frame.config(bg='#f0f0f0')
    options_frame.config(bg='#f0f0f0')
    addc_btn.config(bg="#f0f0f0", activebackground="#f0f0f0")
    br_btn.config(bg="#f0f0f0", activebackground="#f0f0f0")
    the_btn.config(bg="#f0f0f0", command=switch_to_night,
                   activebackground="#f0f0f0", image=d_img)
    if main_open:
        test_btn.config(bg="#f0f0f0", fg="black")
        testall_btn.config(bg="#f0f0f0", fg="black")
        ref_btn.config(bg="#f0f0f0", activebackground="#f0f0f0")
    if win2_open:
        frame2.config(bg='#f0f0f0')
        drop.config(bg='#f0f0f0', fg='black')
    if win3_open:
        win3.config(bg='#f0f0f0')
        left_frame.config(bg='#f0f0f0')
        right_frame.config(bg='#f0f0f0')
        red_radio.config(bg='#ed493e', activebackground='#ed493e')
        or_radio.config(bg='#f08e32', activebackground='#f08e32')
        bl_radio.config(bg='#36a8eb', activebackground='#36a8eb')
        gr_radio.config(bg='#00d05e', activebackground='#00d05e')
        front_edit.config(bg='white')
        back_edit.config(bg='white')
        notes_edit.config(bg='white')
        search_entry.config(bg='white')
        boxes_frame.config(bg='#f0f0f0')
        ed_del_frame.config(bg='#f0f0f0')
        flag_frame.config(bg='#f0f0f0')
        win3.config(bg='#f0f0f0')
        sp1.config(bg='#f0f0f0')
        sp2.config(bg='#f0f0f0')
        sp3.config(bg='#f0f0f0')
        sp4.config(bg='#f0f0f0')
        spacee_label.config(bg='#f0f0f0')
        s_label.config(bg='#f0f0f0', image=sd_img)
        flag_radio.config(bg='#f0f0f0', fg='black')
        dupl_btn.config(bg='#f0f0f0', fg='black')
        edit_btn.config(bg='#f0f0f0', image=edd_img)
        delete_btn.config(bg='#f0f0f0')

    if test_open:
        front_show.config(bg='#f0f0f0', fg='black')
        show_btn.config(bg='#f0f0f0', image=show_picl,
                        activebackground='#f0f0f0')
        back_show.config(bg='#f0f0f0')
        notes_show.config(bg='#f0f0f0')
        back_btn.config(bg='#f0f0f0', activebackground='#f0f0f0')
        label_space.config(bg='#f0f0f0')
    if deck_win_open:
        rev_lb.config(bg='#f0f0f0')
        alg_lb.config(bg='#f0f0f0')
        deck_label.config(bg='#f0f0f0', fg='black')
        abtn.config(bg='#f0f0f0', fg='black')
        deck_entry.config(bg='white')
        yes_btn.config(bg='#f0f0f0', fg='black',
                       selectcolor='white', activebackground='#f0f0f0')
        no_btn.config(bg='#f0f0f0', fg='black',
                      selectcolor='white', activebackground='#f0f0f0')
        more_btn.config(bg='#f0f0f0', fg='black',
                        selectcolor='white', activebackground='#f0f0f0')
        less_btn.config(bg='#f0f0f0', fg='black',
                        selectcolor='white', activebackground='#f0f0f0')
    if add_win_open:
        b_label.config(bg='#f0f0f0', fg='black')
        f_label.config(bg='#f0f0f0', fg='black')
        n_label.config(bg='#f0f0f0', fg='black')
        add_btn.config(bg='#f0f0f0', fg='black')
        entry_front.config(bg='white')
        entry_back.config(bg='white')
        entry_notes.config(bg='white')
    if test2_open:
        radios_frame.config(bg='#f0f0f0')
        fo_radio.config(bg='#f0f0f0', fg='black',
                        activebackground='#f0f0f0', selectcolor='white')
        vh_radio.config(bg='#f0f0f0', fg='black',
                        activebackground='#f0f0f0', selectcolor='white')
        ha_radio.config(bg='#f0f0f0', fg='black',
                        activebackground='#f0f0f0', selectcolor='white')
        go_radio.config(bg='#f0f0f0', fg='black',
                        activebackground='#f0f0f0', selectcolor='white')
        ea_radio.config(bg='#f0f0f0', fg='black',
                        activebackground='#f0f0f0', selectcolor='white')
        back_btn.config(bg='#f0f0f0', activebackground='#f0f0f0')
        label_space.config(bg='#f0f0f0')
        spa1.config(bg='#f0f0f0')
        spa2.config(bg='#f0f0f0')
        spa3.config(bg='#f0f0f0')
        spa4.config(bg='#f0f0f0')
        ch_label.config(bg='#f0f0f0')
        show_btn.config(image=ne_pic, command=done_func, borderwidth=0, activebackground='#f0f0f0',
                        bg='#f0f0f0')
        front_show.config(bg='#f0f0f0', fg='black')
        back_show.config(text=b, bg='#f0f0f0', fg='black')
        notes_show.config(text=n, bg='#f0f0f0', fg='black')
    stylish.configure("Treeview", background='white',
                      foreground='black', fieldbackground='white')
    c.execute("update data set theme='light'")
    mydb.commit()


def add_dem_cards():
    '''
    Creates add card / create deck window.
    '''
    global win2, win2_open
    if not win2_open:
        win2 = Toplevel()
        win2.title('Add Cards/Decks')
        win2.geometry('425x425+925+40')
        win2.iconbitmap('plus.ico')
        win2.resizable(False, False)
        win2_open = True
        win2.protocol("WM_DELETE_WINDOW", check_close_win2)

        global frame2
        frame2 = Frame(win2)
        frame2.pack(fill='both', expand=True)

        create_drop('Choose Deck')
    else:
        win2.lift()


def check_close_win2():
    '''
    Destroys add card / create deck window.
    '''
    global win2_open, add_win_open, deck_win_open
    win2_open = False
    add_win_open = False
    deck_win_open = False
    win2.destroy()


def create_drop(var):
    '''
    Creates dropdown menu in the add card / create deck window.
    '''
    global drop, clicked
    helv10 = font.Font(family=font_names[1], size=10)
    clicked = StringVar()
    clicked.set(f'{var}')
    deck_lst.append("Add deck")
    drop = OptionMenu(frame2, clicked, *deck_lst, command=selection)
    drop['menu'].configure(activebackground='#f6738c')
    drop.place(relx=0, rely=0)
    drop.config(font=helv10)
    menu = frame2.nametowidget(drop.menuname) # To get the widget object(in this case, the 'names in the menu') to change fonts in the drop down menu
    menu.config(font=helv10)
    deck_lst.remove("Add deck")

    if night_mode_on:
        frame2.config(bg='#121212')
        drop.config(bg='#121212', fg='white')


def browse_cards():
    '''
    Logic for browsing cards display creation.
    '''
    global win3, win3_open, right_frame
    if not win3_open:
        win3 = Toplevel()
        win3.title('Browse Cards')
        win3.geometry('700x700+0+0')
        win3.state('zoomed')
        win3.iconbitmap('browse.ico')
        win3_open = True
        win3.protocol("WM_DELETE_WINDOW", check_close_win3)

        create_lframe()

        global right_frame, tree_frame, search_entry, search_tree, front_edit, back_edit, notes_edit, edit_btn, delete_btn, flag_selection, dupl_btn, boxes_frame, ed_del_frame, sp1, sp2, sp3, sp4, s_label, flag_radio, red_radio, or_radio, gr_radio, bl_radio, no_radio, flag_frame, sl_img, spacee_label, sd_img, edl_img, edd_img, del_img, night_mode_on

        right_frame = Frame(win3)
        right_frame.place(relx=0.35, rely=0)

        spacee_label = Label(right_frame)
        spacee_label.pack(pady=15)

        sl_img = PhotoImage(file='search_light.png')
        sd_img = PhotoImage(file='search_dark.png')
        s_label = Label(right_frame, image=sl_img)
        s_label.place(relx=0.35, rely=0.01)
        Hovertip(s_label, 'Search')

        search_entry = Entry(right_frame, borderwidth=5)
        search_entry.place(relx=0.42, rely=0.03)
        search_entry.bind("<KeyRelease>", check)

        tree_frame = Frame(right_frame)
        tree_frame.pack(pady=15)

        create_stree()

        boxes_frame = Frame(right_frame)
        boxes_frame.pack(pady=10)

        front_edit = Entry(boxes_frame, width=15, font=(
            font_names[1], 12), borderwidth=2, justify='center')
        front_edit.grid(row=0, column=0, padx=20, ipady=5)

        back_edit = Entry(boxes_frame, width=15, font=(
            font_names[1], 12), borderwidth=2, justify='center')
        back_edit.grid(row=0, column=1, padx=20, ipady=5)

        notes_frame = Frame(right_frame)
        notes_frame.pack(pady=10)

        notes_edit = Text(notes_frame, width=35, font=(
            font_names[1], 10), height=2)
        notes_edit.pack(ipady=3)

        dupl_btn = Button(right_frame, text="Find Duplicates", borderwidth=3,
                          font=(font_names[0], 9), command=dupl_func)
        dupl_btn['state'] = DISABLED
        dupl_btn.pack()

        flag_radio = Label(right_frame, text='Flags',
                           font=(font_names[1], 12, 'bold'))
        flag_radio.pack(pady=10)

        flag_frame = Frame(right_frame)
        flag_frame.pack()

        flag_selection = StringVar()

        red_radio = Radiobutton(flag_frame, text='Red', takefocus=0, font=(font_names[1], 11, 'bold'), bg='#ed493e', fg='white', selectcolor='#121212', activebackground='#ed493e',
                                variable=flag_selection, value='red')
        red_radio.grid(row=0, column=0)

        sp1 = Label(flag_frame, text='        ')
        sp1.grid(row=0, column=1)

        or_radio = Radiobutton(flag_frame, text='Orange', takefocus=0, font=(font_names[1], 11, 'bold'), bg='#f08e32', fg='white', selectcolor='#121212', activebackground='#f08e32',
                               variable=flag_selection, value='orange')
        or_radio.grid(row=0, column=2)

        sp2 = Label(flag_frame, text='     ')
        sp2.grid(row=0, column=3)

        bl_radio = Radiobutton(flag_frame, text='Blue', takefocus=0, font=(font_names[1], 11, 'bold'), bg='#36a8eb', fg='white', selectcolor='#121212', activebackground='#36a8eb',
                               variable=flag_selection, value='blue')
        bl_radio.grid(row=0, column=4)

        sp3 = Label(flag_frame, text='     ')
        sp3.grid(row=0, column=5)

        gr_radio = Radiobutton(flag_frame, text='Green', takefocus=0, font=(font_names[1], 11, 'bold'), bg='#00d05e', fg='white', selectcolor='#121212', activebackground='#00d05e',
                               variable=flag_selection, value='green')
        gr_radio.grid(row=0, column=6)

        sp4 = Label(flag_frame, text='     ')
        sp4.grid(row=0, column=7)

        no_radio = Radiobutton(flag_frame, text='No Flag', takefocus=0, font=(font_names[1], 11, 'bold'), bg='#2e2e2e', fg='white', selectcolor='#121212', activebackground='#2e2e2e',
                               variable=flag_selection, value='no flag')
        no_radio.grid(row=0, column=8)
        flag_selection.set(None)

        ed_del_frame = Frame(right_frame)
        ed_del_frame.pack(pady=15)

        edl_img = PhotoImage(file='savelight.png')
        edd_img = PhotoImage(file='savedark.png')
        edit_btn = Button(ed_del_frame, image=edl_img,
                          command=edit_card, borderwidth=0)
        edit_btn['state'] = DISABLED
        edit_btn.grid(row=0, column=0, padx=20)
        Hovertip(edit_btn, 'Save')

        del_img = PhotoImage(file='delete.png')
        delete_btn = Button(ed_del_frame, image=del_img,
                            command=delete_card, borderwidth=0)
        delete_btn['state'] = DISABLED
        delete_btn.grid(row=0, column=1, padx=20)
        Hovertip(delete_btn, 'Delete')

        if night_mode_on:
            red_radio.config(bg='#da383e', activebackground='#da383e')
            or_radio.config(bg='#f08e32', activebackground='#f08e32')
            bl_radio.config(bg='#36a1eb', activebackground='#36a1eb')
            gr_radio.config(bg='#32ae8a', activebackground='#32ae8a')
            no_radio.config(bg='#2e2e2e', activebackground='#2e2e2e')
            front_edit.config(bg='#ababab')
            back_edit.config(bg='#ababab')
            notes_edit.config(bg='#ababab')
            search_entry.config(bg='#ababab')
            right_frame.config(bg='#121212')
            left_frame.config(bg='#121212')
            boxes_frame.config(bg='#121212')
            ed_del_frame.config(bg='#121212')
            flag_frame.config(bg='#121212')
            win3.config(bg='#121212')
            sp1.config(bg='#121212')
            sp2.config(bg='#121212')
            sp3.config(bg='#121212')
            sp4.config(bg='#121212')
            spacee_label.config(bg='#121212')
            s_label.config(bg='#121212', image=sd_img)
            flag_radio.config(bg='#121212', fg='#a87ae0')
            dupl_btn.config(bg='#bb8bfc', fg='black')
            edit_btn.config(bg='#121212', image=edd_img)
            delete_btn.config(bg='#121212')

    else:
        win3.lift()


def create_lframe():
    global decks_list, card_state, flag_lst, left_frame

    left_frame = Frame(win3)
    left_frame.place(relx=0.05, rely=0)

    deck_lst.append("No Deck Chosen")
    decks_list = ttk.Combobox(
        left_frame, value=deck_lst, justify='center', font=(font_names[1], '10'))
    decks_list.option_add('*TCombobox*Listbox.Justify', 'center')
    decks_list.option_add('*TCombobox*Listbox.selectBackground', '#f6738c')
    decks_list.set("No Deck Chosen")
    decks_list.bind("<<ComboboxSelected>>", update_cards)
    decks_list.pack(padx=10, pady=100, ipadx=50)
    deck_lst.remove("No Deck Chosen")

    usefont = font.Font(family=font_names[1], size=0)
    flag_lst = ttk.Combobox(
        left_frame, value=['Red', 'Orange', 'Green', 'Blue', 'No Flag Chosen'], justify='center', font=(font_names[1], '10'))
    flag_lst.option_add("*TCombobox*Listbox*font", (font_names[1], '10'))
    flag_lst.option_add('*TCombobox*Listbox.Justify', 'center')
    flag_lst.option_add('*TCombobox*Listbox.selectBackground', '#f6738c')
    flag_lst.set("No Flag Chosen")
    flag_lst.bind("<<ComboboxSelected>>", update_cards)
    flag_lst.pack(padx=10, pady=100, ipadx=50)
    card_state = ttk.Combobox(
        left_frame, value=['New', 'Learning', 'Card State'], justify='center', font=(font_names[1], '10'))
    card_state.option_add('*TCombobox*Listbox.Justify', 'center')
    card_state.option_add('*TCombobox*Listbox.selectBackground', '#f6738c')
    card_state.set("Card State")
    card_state.bind("<<ComboboxSelected>>", update_cards)
    card_state.pack(padx=10, pady=100, ipadx=50)


def check_close_win3():
    '''
    Closes the browsing cards window.
    '''
    global win3_open
    win3_open = False
    win3.destroy()


def fill_boxes(event):
    '''
    Fills edit boxes for cards.
    '''
    if search_tree.selection():
        id = search_tree.selection()[0]
        global fill_
        fill_ = search_tree.set(id)
        front_fill = fill_["Front"]
        back_fill = fill_["Back"]
        h = 'deck_' + f"{decks_list.get()}"
        try:
            c.execute(
                f"select notes,flags from {h} where uk_id = '{fill_['uk_id']}'")
        except:
            pass
        global notes_flag_id
        notes_flag_id = ''
        for i in c:
            notes_flag_id = i

        front_edit.delete(0, END)
        back_edit.delete(0, END)
        notes_edit.delete('1.0', END)
        front_edit.insert(0, front_fill)
        back_edit.insert(0, back_fill)
        if notes_flag_id:
            notes_edit.insert('1.0', notes_flag_id[0])
            if notes_flag_id[1]:
                flag_selection.set(notes_flag_id[1])
            else:
                flag_selection.set(None)

        edit_btn['state'] = NORMAL
        delete_btn['state'] = NORMAL
        dupl_btn['state'] = NORMAL


def dupl_func():
    '''
    Function to find duplicate cards among the selected deck.
    '''
    edit_btn['state'] = DISABLED
    delete_btn['state'] = DISABLED
    dupl_btn['state'] = DISABLED
    front_edit.delete(0, END)
    back_edit.delete(0, END)
    notes_edit.delete('1.0', END)
    flag_selection.set(None)
    if search_tree.selection():
        cards = []
        id = search_tree.selection()[0]
        selected_card = search_tree.set(id)
        for deck in deck_lst:
            h = 'deck_' + f"{deck[0]}"
            try:
                c.execute(
                    f"select front,back,uk_id,flags from {h} where front = '{selected_card['Front']}' and back = '{selected_card['Back']}'")
            except:
                pass
            for i in c:
                # print(i)
                if selected_card['uk_id'] != i[2]:
                    cards.append(i)
    update_tree(cards)


def edit_card():
    '''
    Edits selected card based on user input.
    '''
    edit_btn['state'] = DISABLED
    delete_btn['state'] = DISABLED
    dupl_btn['state'] = DISABLED
    if front_edit.get():
        h = 'deck_' + f"{decks_list.get()}"
        try:
            c.execute(
                f"update {h} set flags = '{flag_selection.get()}',notes = '{notes_edit.get('1.0', END)}',front = '{front_edit.get()}',back = '{back_edit.get()}' where uk_id = '{fill_['uk_id']}' ")
        except:
            pass
        mydb.commit()
        update_cards(card_state.get())
        update_cards(decks_list.get())
        update_cards(flag_lst.get())
    else:
        messagebox.showerror("Empty Card Front!",
                             'The front of a card cannot be empty')


def delete_card():
    '''
    Deletes selected card.
    '''
    global recent_cards
    front_edit.delete(0, END)
    back_edit.delete(0, END)
    notes_edit.delete('1.0', END)
    flag_selection.set(None)

    edit_btn['state'] = DISABLED
    delete_btn['state'] = DISABLED
    dupl_btn['state'] = DISABLED
    h = 'deck_' + f"{decks_list.get()}"
    c.execute(
        f"delete from {h} where uk_id = '{fill_['uk_id']}'")

    cards_to_use = []
    cards_to_use = [i for i in recent_cards if i[2] != fill_['uk_id']]

    update_tree(cards_to_use)


def update_cards(event):
    '''
    Fetches up to date information from database about cards (browsing window).
    '''
    global recent_cards
    h = 'deck_' + f"{decks_list.get()}"
    cards = []
    front_edit.delete(0, END)
    back_edit.delete(0, END)
    notes_edit.delete('1.0', END)
    flag_selection.set(None)
    if decks_list.get() != "No Deck Chosen":
        if flag_lst.get() != "No Flag Chosen":
            if card_state.get() != "Card State":
                c.execute(
                    f"select front,back,uk_id,flags from {h} where flags = '{flag_lst.get()}' and card_state = '{card_state.get()}'")
            else:
                c.execute(
                    f"select front,back,uk_id,flags from {h} where flags = '{flag_lst.get()}'")
        else:
            if card_state.get() != "Card State":
                c.execute(
                    f"select front,back,uk_id,flags from {h} where card_state = '{card_state.get()}'")
            else:
                c.execute(
                    f"select front,back,uk_id,flags from {h}")
        for i in c:
            cards.append(i)
    else:
        if flag_lst.get() != "No Flag Chosen":
            if card_state.get() != "Card State":
                for deck in deck_lst:
                    h = 'deck_' + f"{deck[0]}"
                    c.execute(
                        f"select front,back,uk_id,flags from {h} where flags = '{flag_lst.get()}' and card_state = '{card_state.get()}'")
                    for i in c:
                        cards.append(i)
            else:
                for deck in deck_lst:
                    h = 'deck_' + f"{deck[0]}"
                    c.execute(
                        f"select front,back,uk_id,flags from {h} where flags = '{flag_lst.get()}'")
                    for i in c:
                        cards.append(i)
        else:
            if card_state.get() != "Card State":
                for deck in deck_lst:
                    h = 'deck_' + f"{deck[0]}"
                    c.execute(
                        f"select front,back,uk_id,flags from {h} where card_state = '{card_state.get()}'")
                    for i in c:
                        cards.append(i)
    recent_cards = cards
    update_tree(cards)


def update_tree(cards):
    global night_mode_on
    '''
    Updates the display for the browse cards window.
    '''
    search_tree.delete(*search_tree.get_children())

    count = 0
    for r in cards:
        # print(r)
        if r[3] == 'green':
            search_tree.insert(parent='', index='end', iid=count, tags='green',
                               text='', values=(r[0], r[1], r[2]))
        elif r[3] == 'red':
            search_tree.insert(parent='', index='end', iid=count, tags='red',
                               text='', values=(r[0], r[1], r[2]))
        elif r[3] == 'blue':
            search_tree.insert(parent='', index='end', iid=count, tags='blue',
                               text='', values=(r[0], r[1], r[2]))
        elif r[3] == 'orange':
            search_tree.insert(parent='', index='end', iid=count, tags='orange',
                               text='', values=(r[0], r[1], r[2]))
        else:
            search_tree.insert(parent='', index='end', iid=count, tags='none',
                               text='', values=(r[0], r[1], r[2]))

        count += 1
    search_tree.tag_configure(
        'green', foreground='#00aa32', font=(font_names[1], 10, 'bold'))
    search_tree.tag_configure(
        'red', foreground='#da383e', font=(font_names[1], 10, 'bold'))
    search_tree.tag_configure(
        'blue', foreground='#0067ff', font=(font_names[1], 10, 'bold'))
    search_tree.tag_configure(
        'orange', foreground='#f08e32', font=(font_names[1], 10, 'bold'))
    search_tree.tag_configure(
        'none', font=(font_names[1], 10, 'bold'))


def selection(event):
    '''
    Contains logic to get information about new cards and new decks.
    '''
    clear_frame(frame2)
    global add_win_open, deck_win_open
    if event == "Add deck":
        global deck_entry, alg_choice, deck_label, s1, s2, more_btn, less_btn, yes_btn, no_btn, clicked, alg_pic, rev_pic, alg_lb, rev_lb
        deck_win_open = True
        add_win_open = False
        create_drop('Add Deck')

        deck_label = Label(frame2, text="Deck", font=(font_names[1], 12))
        deck_label.place(relx=0.45, rely=0.05)

        deck_entry = Entry(frame2, width=20, borderwidth=3,
                           justify=CENTER, font=(font_names[1], 10))
        deck_entry.bind('<KeyRelease>', revive_abtn)
        deck_entry.place(relx=0.325, rely=0.11)

        alg_pic = PhotoImage(file='operation.png')
        alg_lb = Label(frame2, image=alg_pic)
        alg_lb.place(relx=0.45, rely=0.21)

        alg_choice = StringVar()
        more_btn = Radiobutton(frame2, text='More Intensive Learning', takefocus=0, font=(font_names[1], 9),
                               variable=alg_choice, value='more', command=lambda: revive_abtn(event))
        more_btn.place(relx=0.3, rely=0.31)

        less_btn = Radiobutton(frame2, text='Less Intensive Learning', takefocus=0, font=(font_names[1], 9),
                               variable=alg_choice, value='less', command=lambda: revive_abtn(event))
        less_btn.place(relx=0.31, rely=0.37)
        alg_choice.set(None)

        global rev_or_not, abtn
        rev_pic = PhotoImage(file='exchange.png')
        rev_lb = Label(frame2, image=rev_pic)
        rev_lb.place(relx=0.45, rely=0.47)

        rev_or_not = StringVar()
        yes_btn = Radiobutton(frame2, text='Allow reverse cards', takefocus=0, font=(font_names[1], 9),
                              variable=rev_or_not, value='yes', command=lambda: revive_abtn(event))
        yes_btn.place(relx=0.32, rely=0.57)

        no_btn = Radiobutton(frame2, text="Don't allow reverse cards", takefocus=0, font=(font_names[1], 9),
                             variable=rev_or_not, value='no', command=lambda: revive_abtn(event))
        no_btn.place(relx=0.3, rely=0.63)
        rev_or_not.set(None)
        abtn = Button(frame2, text='Add', command=add_deck)
        abtn['state'] = DISABLED
        abtn.place(relx=0.46, rely=0.73)

        if night_mode_on:
            rev_lb.config(bg='#121212')
            alg_lb.config(bg='#121212')
            deck_label.config(bg='#121212', fg='#a87ae0')
            abtn.config(bg='#bb8bfc', fg='black')
            deck_entry.config(bg='#ababab')
            yes_btn.config(bg='#121212', fg='white',
                           selectcolor='#6213a8', activebackground='#121212')
            no_btn.config(bg='#121212', fg='white',
                          selectcolor='#6213a8', activebackground='#121212')
            more_btn.config(bg='#121212', fg='white',
                            selectcolor='#6213a8', activebackground='#121212')
            less_btn.config(bg='#121212', fg='white',
                            selectcolor='#6213a8', activebackground='#121212')

    else:
        global deck_to_use
        add_win_open = True
        deck_win_open = False
        for i in deck_lst:
            deck_to_use = event[0]
            if deck_to_use == i[0]:
                global entry_front, entry_back, entry_notes, add_btn, b_label, f_label, n_label
                create_drop(f'{deck_to_use}')
                f_label = Label(frame2, text="Front", font=(font_names[1], 12))
                f_label.place(relx=0.45, rely=0.1)
                entry_front = Entry(
                    frame2, borderwidth=3, font=(font_names[1], 10), justify=CENTER)
                entry_front.bind('<KeyRelease>', revive_addbtn)
                entry_front.place(relx=0.325, rely=0.175)

                b_label = Label(frame2, text="Back", font=(font_names[1], 12))
                b_label.place(relx=0.45, rely=0.3)

                entry_back = Entry(
                    frame2, borderwidth=3, font=(font_names[1], 10), justify=CENTER)
                entry_back.bind('<KeyRelease>', revive_addbtn)
                entry_back.place(relx=0.325, rely=0.375)

                n_label = Label(frame2, text="Notes", font=(font_names[1], 12))
                n_label.place(relx=0.45, rely=0.475)

                entry_notes = Text(
                    frame2, width=50, height=3, font=(font_names[1], 10))
                entry_notes.place(relx=0.075, rely=0.55)

                add_btn = Button(frame2, text='Add', command=add_cards)
                add_btn['state'] = DISABLED
                add_btn.place(relx=0.46, rely=0.7)
        if night_mode_on:
            b_label.config(bg='#121212', fg='#a87ae0')
            f_label.config(bg='#121212', fg='#a87ae0')
            n_label.config(bg='#121212', fg='#a87ae0')
            add_btn.config(bg='#bb8bfc', fg='black')
            entry_front.config(bg='#ababab')
            entry_back.config(bg='#ababab')
            entry_notes.config(bg='#ababab')


def revive_addbtn(event):
    '''
    Changes button state based its current state.
    '''
    if entry_front.get() and entry_back.get():
        add_btn['state'] = NORMAL
    else:
        add_btn['state'] = DISABLED


def revive_abtn(event):
    '''
    Changes button state based its current state.
    '''
    if deck_entry.get() and (f"{alg_choice.get()}" != 'None' or not f"{alg_choice.get()}") and (f"{rev_or_not.get()}" != 'None' or not f"{rev_or_not.get()}"):
        abtn['state'] = NORMAL
    else:
        abtn['state'] = DISABLED


def add_deck():
    '''
    Logic for creating a new deck (table) in the database.
    '''
    global rev_or_not, alg_choice, drop, win2, win3_open
    h = 'deck_' + deck_entry.get()
    c.execute(f"select name from decks")
    x = []
    for i in c:
        x += i
    if deck_entry.get() in x:
        messagebox.showerror(
            "Duplicate Deck!", "Decks with same names not allowed")
        win2.lift()
    else:
        c.execute(
            f"insert into decks values('{deck_entry.get()}','{alg_choice.get()}','{rev_or_not.get()}')")
        c.execute(f"create table {h}(front varchar(20),back varchar(100),notes varchar(500),flags char(20),card_state char(20),unlock_time varchar(100),last_interval varchar(100),lock_time varchar(100),uk_id char(32) unique)")
        deck_entry.delete(0, END)
        deck_entry.focus_set()
        mydb.commit()
        clear_frame(frame)
        create_tree(frame)
        drop.destroy()
        deck_lst.append("Add deck")
        drop = OptionMenu(frame2, clicked, *deck_lst, command=selection)
        drop.place(relx=0, rely=0)
        deck_lst.remove("Add deck")

        update_decks()

        rev_or_not.set(None)
        alg_choice.set(None)


def add_cards():
    '''
    Logic for creating new card (row) in the chosen deck.
    '''
    global win3_open
    l = [deck_to_use, entry_front.get(), entry_back.get(), entry_notes.get('1.0', END).strip(),
         str(current_time_listobj()), '[0,0,0,0,5,0]', str(current_time_listobj())]
    h = 'deck_' + f"{deck_to_use}"
    c.execute(f"select uk_id from {h}")
    keys = []
    for i in c:
        keys.append(i[0])
    while True:
        s = secrets.token_hex(16)
        if s not in keys:
            break
    h = 'deck_' + f"{l[0]}"
    c.execute(
        f"insert into {h}(front,back,notes,unlock_time,last_interval,lock_time,uk_id,card_state,flags) values('{l[1]}','{l[2]}','{l[3]}','{l[4]}','{l[5]}','{l[6]}','{s}','New','None')")
    mydb.commit()
    entry_front.delete(0, END)
    entry_back.delete(0, END)
    entry_notes.delete('1.0', END)
    entry_front.focus_set()
    clear_frame(frame)
    create_tree(frame)

    if win3_open:
        update_cards(card_state.get())
        update_cards(decks_list.get())
        update_cards(flag_lst.get())

    update_decks()


def check(event):
    '''
    Logic for searching among the cards and returning results.
    '''
    global recent_cards
    var = search_entry.get()
    if var:
        data = []
        if recent_cards:
            for i in recent_cards:
                if var.lower() in i[0].lower() or var.lower() in i[1].lower():
                    data.append(i)
        update_tree(data)
    else:
        update_cards(decks_list.get())
        update_cards(flag_lst.get())
        update_cards(card_state.get())


def clearData():
    '''
    Deletes account of current user (1 database)
    '''
    global db_name, win3_open, win2_open, frame, main_open, night_mode_on, stylish, main_menu
    conf = messagebox.askyesno(
        "Delete account and lose all data?", "This account will be permanently deleted.")
    if conf:
        c.execute(f'drop database if exists {db_name}')
        if win2_open:
            win2.destroy()
        if win3_open:
            win3.destroy()
        main_menu.destroy()
        clear_frame(options_frame)
        ref_btn.destroy()
        options_frame.config(bg='#f0f0f0')
        frame.destroy()
        stylish.configure("Treeview", background='white',
                          foreground='black', fieldbackground='white')
        root.config(bg='#f0f0f0')
        create_main_screen()
        db_name = None


def clearAccount():
    '''
    Clear account data (one user only)
    '''
    global db_name
    conf = messagebox.askyesno(
        "Clear account and lose all data?", "The contents of this account will be permanently deleted.")
    if conf:
        c.execute(f'use {db_name}')
        c.execute(f'show tables')
        tables = []
        for i in c:
            if i[0].startswith('deck_'):
                tables.append(i[0])
        for i in tables:
            c.execute(f'drop table {i}')
        c.execute('truncate decks')
        back_func()

# / setting up an auto uptdate function for refreshing main display


def auto_refresh():
    global tree_frame, win3_open, ref_img, night_mode_on, ref_btn
    update_decks()
    if test_open == False:
        clear_frame(frame)
        create_tree(frame)
        ref_btn = Button(root, image=ref_img, command=refresh, borderwidth=0)
        if night_mode_on:
            ref_btn.config(bg='#121212', activebackground='#121212')
        ref_btn.place(relx=0.965, rely=0.02)
        # print('refreshed')


def every(delay, task):
    global t
    next_time = time.time() + delay
    while True:
        time.sleep(max(0, next_time - time.time()))
        try:
            if db_name and not test_open and not test2_open:
                task()
        except Exception:
            traceback.print_exc()
        next_time += (time.time() - next_time) // delay * delay + delay


t = threading.Thread(target=lambda: every(15, task=lambda: auto_refresh())
                     )  # / 15 seconds before each refresh
t.daemon = True  # / Daemon threads are those which are killed as soon as the program finishes
t.start()

# / Deploying the login screen


create_main_screen()

# /Setting update loop for tkinter

root.mainloop()
