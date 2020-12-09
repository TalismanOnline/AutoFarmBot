import pyautogui as autofarm
import time
import logging
import imghdr
from datetime import datetime
from ReadWriteMemory import ReadWriteMemory
from humanfriendly import format_timespan
import smtplib
from email.message import EmailMessage
from configparser import ConfigParser
import sys
import os

# Attaching to config.ini
config = ConfigParser()
config.read('config.ini')

# Setting up log file
LogFileName = datetime.now().strftime("log\\AutoFarmLog - %d_%m_%Y - Started at %Hh%Mm.txt")
logging.basicConfig(filename=LogFileName, level=logging.INFO, format='%(message)s')

# Variables
global MaximumHP, MaximumMana, CharClass, SendEmail, SendEmailAtEveryXMobKill
global FarmingSpotTimer, StartingTime, AutoPick, BattleTime, RemainingTime, RunningTime
global InitialCurrentXP, XpToNextLvl, PreviousXP, XpDifference, ActualXPPercentage
global RemainingXP, CurrentXP, XpPercentage, AutobuffAtEveryXMobKill, AutoBuffScript, AutoBuff
global UseHpPotionPercentage, UseManaPotionPercentage, HpPotionQuantity, MpPotionQuantity
global SendToEmailAddress

MobCount = 1
CurrentHP = 1
MaxHP = 1
HPPercentage = 1
ManaPercentage = 1
CurrentMana = 1
MaxMana = 1
TotalXpEarned = 0
PickupButton = 'None'

# Attach to Talisman Online process
rwm = ReadWriteMemory()
Process = rwm.get_process_by_name('client.exe')
Process.open()

# Pointers
HealthPointer = Process.get_pointer(0x00400000 + 0x00D1EB80, offsets=[0x3B8])
ManaPointer = Process.get_pointer(0x00400000 + 0x00D1EB80, offsets=[0x64, 0x30, 0x7E8, 0x1D4, 0x3BC])
SelectedEnemyPointer = Process.get_pointer(0x00400000 + 0x00C1D96C, offsets=[0x10, 0x2C, 0x9F4, 0xC, 0x24, 0x18, 0x240])
TargetNamePointer = Process.get_pointer(0x00400000 + 0x00EA7B78, offsets=[0x18, 0x16C, 0x0, 0xC, 0x47C, 0x80, 0x4D4])
CurrentXPPointer = Process.get_pointer(0x00400000 + 0x00BFB980, offsets=[0x6D0])
EnemyHpPointer = Process.get_pointer(0x00400000 + 0x00EA7B78,
                                     offsets=[0x18, 0x59C, 0x0, 0xC, 0x1F4, 0x50, 0x28, 0x224,
                                              0x50, 0x460, 0x918])


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def get_char_info():
    global HPPercentage, CurrentHP, MaxHP, ManaPercentage, CurrentMana, MaxMana, XpPercentage, CurrentXP, XpToNextLvl

    try:
        # HP Status
        Health = Process.read(HealthPointer)

        CurrentHP = int(Health)
        MaxHP = int(MaximumHP)
        HPPercentage = (int(CurrentHP) / int(MaxHP) * 100)

        # Mana Status
        if CharClass == 'Mage':
            Mana = Process.read(ManaPointer)

            CurrentMana = int(Mana)
            MaxMana = int(MaximumMana)
            ManaPercentage = (int(CurrentMana) / int(MaxMana) * 100)

        # XP Status
        Experience = Process.read(CurrentXPPointer)

        CurrentXP = int(Experience)
        XpPercentage = (CurrentXP / XpToNextLvl) * 100

    except ():
        HPPercentage = 100


def show_char_info():
    global HPPercentage, CurrentHP, MaxHP, ManaPercentage, CurrentMana, MaxMana, XpPercentage, CurrentXP, XpToNextLvl

    get_char_info()

    if HPPercentage > 101:
        print_and_log("<< WARNING: char was not full HP when bot started! Please, restart AutoFarm with full HP/MP. >>")
        print_and_log("<< (Or did your char just leveled up?) >>")
        spacer()
    else:
        print_and_log("...---====== CHAR INFO ======---...")
        print_and_log("HP: [" + str(CurrentHP) + " / " + str(MaxHP) + "] - [" + '%.2f%%' % HPPercentage + "]")

        if CharClass == 'Mage':
            print_and_log("MP: [" + str(CurrentMana) + " / " + str(MaxMana) + "] - [" + '%.2f%%' % ManaPercentage + "]")

        print_and_log('-')
        print_and_log("XP: [" + str(CurrentXP) + " / " + str(XpToNextLvl) + "] - [" + '%.4f%%' % XpPercentage + "]")
        print_and_log("'''---=======================---'''")


def calculate_initial_experience():
    global XpToNextLvl, PreviousXP, RemainingXP

    Experience = Process.read(CurrentXPPointer)

    CurXP = int(Experience)
    XpToNextLvl = int((CurXP * 100) / ActualXPPercentage)
    PreviousXP = CurXP
    RemainingXP = XpToNextLvl - CurXP


def calculate_experience_difference():
    global XpDifference, PreviousXP, TotalXpEarned, RemainingXP

    wait(0.5)
    Experience = Process.read(CurrentXPPointer)

    CurXP = int(Experience)
    XpDifference = CurXP - PreviousXP
    TotalXpEarned += XpDifference
    PreviousXP = CurXP
    RemainingXP = XpToNextLvl - CurXP


def search_target():
    while True:
        get_char_info()

        if HPPercentage == 0:
            is_char_alive()

        if HPPercentage < 5:
            is_char_alive()

        if HPPercentage < UseHpPotionPercentage:
            wait(3)
            print_and_log("HP < " + str(UseHpPotionPercentage) + "%")
            spacer()
            use_hp_potion()

        if CharClass == 'Mage':
            if ManaPercentage < UseManaPotionPercentage:
                wait(3)
                print_and_log("MP < " + str(UseManaPotionPercentage) + "%")
                spacer()
                use_mp_potion()

        use_skill('tab', 0.8)
        print_and_log('Searching Target...')
        spacer()

        if target_found():
            print_and_log('Target Found!')
            spacer()
            print_and_log('Attacking...')
            spacer()
            break


def target_found():
    SelectedEnemy = Process.read(SelectedEnemyPointer)
    if SelectedEnemy == 391:
        return True


def use_skill(skill, interval):
    autofarm.press(str(skill), interval=float(interval))


def validate_lvl_up():
    global ActualXPPercentage, PreviousXP

    get_char_info()

    if HPPercentage > 101:
        if CurrentHP > MaxHP:
            if CurrentMana > MaxMana:
                wait(1)
                message = (
                        '... - --= == << < L E V E L  U P! >> >= == ---...' +
                        '\n\n<<<< Consider reseting AutoFarm to set Actual XP Percentage correctly! >>>>' +
                        '\n\nReseting Approximate Actual Xp Percentage...' +
                        '\nCalculating Xp To Next Lvl...' +
                        '\nSetting new Max HP / MP values...'
                )

                autofarm.screenshot(resource_path('resources\\AutoFarm_ScreenShot.jpg'), region=(7, 27, 1024, 768))

                send_mail(message)

                print_and_log("...---===<<< L E V E L  U P! >>>===---...")
                NewXpToNextLvl = XpToNextLvl + 1000
                ActualXPPercentage = (CurrentXP / NewXpToNextLvl) * 100
                PreviousXP = CurrentXP
                print_and_log("Reseting Approximate Actual Xp Percentage...")
                print_and_log("For exact Actual Xp Percentage, please reset AutoFarm with right values!")
                calculate_initial_experience()
                print_and_log("Calculating Xp To Next Lvl...")
                set_maximum_hp_mp()
                print_and_log("Setting new Max HP/MP values...")
                print_and_log("...---===<<< L E V E L  U P! >>>===---...")
                spacer()
                wait(1)


def calculate_remaining_time_to_lvl_up():
    global XpDifference, RemainingTime

    if AutoPick is True:
        ExtraTime = 10
    else:
        ExtraTime = 0

    if XpDifference != 0:
        RemainingTime = int((((BattleTime + ExtraTime) * RemainingXP) / XpDifference))
        print_and_log("Approximate time remaining to level up: [" + format_timespan(RemainingTime) + "]")
        spacer()


def is_char_alive():
    deadBoxConfirmLoc = autofarm.locateOnScreen(resource_path('resources\\TO_dead_box_confirmation.png'), confidence=0.9)

    if str(deadBoxConfirmLoc) != 'None':
        if SendEmail is True:
            message = (
                '<<< WARNING: Char Died! >>> ' +
                '\n\nPlease check AutoFarm bot.' +
                '\n\nAlso check if your Star Path is set correctly on the map and check FarmingSpotTimer value.' +
                '\nActual FarmingSpotTimer value is: [' + str(FarmingSpotTimer) + ']'
            )

            autofarm.screenshot(resource_path('resources\\AutoFarm_ScreenShot.jpg'), region=(7, 27, 1024, 768))

            send_mail(message)

        print_and_log('Dead char!')
        okX, okY = autofarm.center(deadBoxConfirmLoc)
        wait(1)

        for seconds in range(3, 0, -1):
            print_and_log("Reviving in " + str(seconds) + " seconds...")
            wait(1)

        spacer()
        wait(1)
        print_and_log('Char revived!')
        spacer()
        autofarm.moveTo(okX, okY)
        wait(1)
        autofarm.click(okX, okY)
        wait(2)
        print_and_log('Evoking Mount... (set to 0 on the skill bar)')
        spacer()
        use_skill(0, 1)
        wait(2)
        goto_farming_spot()
    else:
        print_and_log('Alive char!')
        spacer()


def is_enemy_dead():
    EnemyHp = Process.read(EnemyHpPointer)
    if EnemyHp == 0:
        return True


def use_hp_potion():
    global HpPotionQuantity

    HPPotion = autofarm.locateOnScreen(resource_path('resources\\HPPotion.PNG'), confidence=0.9)
    HPPotionNotOnSkillBar = autofarm.locateOnScreen(resource_path('resources\\HPPotion_NotOnSkillBar.PNG'), confidence=0.9)

    if str(HPPotion) != 'None':
        HpPotionQuantity -= 1
        hpPotionPathX, hpPotionPathY = autofarm.center(HPPotion)
        print_and_log('Using HP Potion...')
        print_and_log('HP Potions left: [' + str(HpPotionQuantity) + ']')
        spacer()
        autofarm.moveTo(hpPotionPathX, hpPotionPathX)
        wait(0.5)
        autofarm.click(hpPotionPathX, hpPotionPathX)
        wait(0.5)
        autofarm.moveTo(hpPotionPathX, hpPotionPathX - 300)

        is_hp_higher_than(95)

    elif str(HPPotionNotOnSkillBar) != 'None':
        HpPotionQuantity -= 1
        hpPotionNSBPathX, hpPotionNSBPathY = autofarm.center(HPPotionNotOnSkillBar)
        print_and_log('Using HP Potion...')
        print_and_log('HP Potions left: [' + str(HpPotionQuantity) + ']')
        spacer()
        autofarm.moveTo(hpPotionNSBPathX, hpPotionNSBPathY)
        wait(0.5)
        autofarm.click(hpPotionNSBPathX, hpPotionNSBPathY)
        wait(0.5)
        autofarm.moveTo(hpPotionNSBPathX, hpPotionNSBPathY - 300)

        is_hp_higher_than(95)

    else:
        print_and_log("HP Potion not found on screen!")
        print_and_log("Sitting Up!")
        spacer()
        is_hp_higher_than(95)


def use_mp_potion():
    global MpPotionQuantity

    MPPotion = autofarm.locateOnScreen(resource_path('resources\\MPPotion.PNG'), confidence=0.9)
    MPPotionNotOnSkillBar = autofarm.locateOnScreen(resource_path('resources\\MPPotion_NotOnSkillBar.PNG'), confidence=0.9)

    if str(MPPotion) != 'None':
        MpPotionQuantity -= 1
        MPPotionPathX, MPPotionPathY = autofarm.center(MPPotion)
        print_and_log('Using MP Potion...')
        print_and_log('MP Potions left: [' + str(MpPotionQuantity) + ']')
        spacer()
        autofarm.moveTo(MPPotionPathX, MPPotionPathX)
        wait(0.5)
        autofarm.click(MPPotionPathX, MPPotionPathX)
        wait(0.5)
        autofarm.moveTo(MPPotionPathX, MPPotionPathX - 300)

        is_mp_higher_than(95)

    elif str(MPPotionNotOnSkillBar) != 'None':
        MpPotionQuantity -= 1
        MPPotionNSBPathX, MPPotionNSBPathY = autofarm.center(MPPotionNotOnSkillBar)
        print_and_log('Using MP Potion...')
        print_and_log('MP Potions left: [' + str(MpPotionQuantity) + ']')
        spacer()
        autofarm.moveTo(MPPotionNSBPathX, MPPotionNSBPathY)
        wait(0.5)
        autofarm.click(MPPotionNSBPathX, MPPotionNSBPathY)
        wait(0.5)
        autofarm.moveTo(MPPotionNSBPathX, MPPotionNSBPathY - 300)

        is_mp_higher_than(95)

    else:
        print_and_log("MP Potion not found on screen!")
        print_and_log("Sitting Up!")
        spacer()
        is_mp_higher_than(95)


def is_hp_higher_than(percent):
    show_char_info()

    for seconds in range(0, 15):
        InitialHP = HPPercentage
        print_and_log("Seconds: " + str(seconds))
        spacer()
        wait(1)
        get_char_info()
        if HPPercentage > percent:
            print_and_log("HP > " + str(percent) + "%. Returning to battle state.")
            show_char_info()
            spacer()
            break

        if HPPercentage < InitialHP:
            print_and_log("Healing Interrupted!")
            spacer()
            break


def is_mp_higher_than(percent):
    show_char_info()

    for seconds in range(0, 15):
        print_and_log("Seconds: " + str(seconds))
        spacer()
        wait(1)
        get_char_info()
        if ManaPercentage > percent:
            print_and_log("MP > " + str(percent) + "%. Returning to battle state.")
            show_char_info()
            spacer()
            break


def goto_farming_spot():
    print_and_log('Finding Star Path Location on map...')
    autofarm.press('m', interval=2)

    while True:
        starPathLoc = autofarm.locateOnScreen(resource_path('resources\\star_point.png'), confidence=0.9)

        if str(starPathLoc) != 'None':
            print_and_log('Star Path Found!')
            spacer()
            starPathX, starPathY = autofarm.center(starPathLoc)
            wait(1)
            print_and_log('Going to the Farming Spot...')
            spacer()
            wait(1)
            autofarm.moveTo(starPathX - 25, starPathY)
            wait(1)
            autofarm.rightClick(starPathX - 25, starPathY)
            wait(1)
            autofarm.moveTo(starPathX, starPathY)
            wait(1)
            autofarm.rightClick(starPathX, starPathY)
            wait(1)
            autofarm.press('m', interval=2)

            for times in range(FarmingSpotTimer, 0, -1):
                print_and_log("Seconds to reach the farming spot: " + str(times))
                wait(1)
                get_char_info()
                if HPPercentage < 5:
                    is_char_alive()

            print_and_log('Unmounting...')
            spacer()
            use_skill(0, 1)
            wait(1)
            print_and_log('Ready to farm again!')
            spacer()
            search_target()
            break
        else:
            print_and_log('Star Path Not Found! Please add one on your Map and check FarmingSpotTimer value!')
            spacer()
            wait(5)


def wait(sec):
    time.sleep(sec)


def spacer():
    print_and_log('-------------')


def starting_announcement():
    spacer()
    print_and_log("Select Talisman Online Window!")
    spacer()
    wait(1)
    for seconds in range(3, 0, -1):
        print_and_log("Bot starting in " + str(seconds) + " seconds.")
        wait(1)
    spacer()
    print_and_log('- Adv. TO AutoFarm by Raaski started. -')
    spacer()


def set_maximum_hp_mp():
    global MaximumHP, MaximumMana
    MaximumHP = Process.read(HealthPointer)
    MaximumMana = Process.read(ManaPointer)


def auto_pick():
    global PickupButton

    InitialHP = HPPercentage

    print_and_log("Searching loot...")
    spacer()
    for x in range(350, 770, 90):
        for y in range(250, 670, 90):
            autofarm.rightClick(x, y)

            PickupButton = autofarm.locateOnScreen(resource_path('resources\\Pickup_Button.PNG'), confidence=0.9, region=(300, 200, 600, 600))
            if str(PickupButton) != 'None':
                wait(1)
                print_and_log("Loot Found! Picking Up...")
                spacer()
                PickupButtonX, PickupButtonY = autofarm.center(PickupButton)
                autofarm.moveTo(PickupButtonX, PickupButtonY)
                wait(1)
                autofarm.click(PickupButtonX, PickupButtonY)
                break

            get_char_info()
            if HPPercentage < InitialHP:
                print_and_log("Looting Interrupted!")
                spacer()
                break
        if str(PickupButton) != 'None':
            break

        if HPPercentage < InitialHP:
            break

    if str(PickupButton) == 'None':
        print_and_log("No Loot Found.")
        spacer()


def print_and_log(text):
    print(text)
    logging.info(text)


def send_mail(message):
    EMAIL_ADDRESS = 'SETYOUREMAILHERE@gmail.com'
    EMAIL_PASSWORD = 'SETYOURPASSWORDHERE'

    msg = EmailMessage()
    msg['Subject'] = 'AutoFarm Update Message - ' + datetime.now().strftime('%d/%m/%Y - %Hh%Mm')
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS
    msg['Bcc'] = SendToEmailAddress
    msg.set_content(message)

    with open(resource_path('resources\\AutoFarm_ScreenShot.jpg'), 'rb') as f:
        file_data = f.read()
        file_type = imghdr.what(f.name)
        file_name = 'AutoFarm_Update'

    msg.add_attachment(file_data, maintype='image', subtype=file_type, filename=file_name)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

    print_and_log("Mail sent to: " + SendToEmailAddress + " - at: " + str(datetime.now()))
    spacer()


def autobuff():
    exec(AutoBuffScript)
    print_and_log('Autobuffing...')
    spacer()


def is_connection_interrupted():
    ConIntHeader = autofarm.locateOnScreen(resource_path('resources\\conn_interrupted_header.png'), confidence=0.9)
    ConIntMessage = autofarm.locateOnScreen(resource_path('resources\\conn_interrupted_message.png'), confidence=0.9)

    if str(ConIntHeader) != 'None':
        if str(ConIntMessage) != 'None':
            ConIntOkButton = autofarm.locateOnScreen(resource_path('resources\\conn_interrupted_ok.png'), confidence=0.9)

            if str(ConIntOkButton) != 'None':
                print_and_log('Connection Interrupted!')
                spacer()

                if SendEmail is True:
                    message = (
                            '<<< WARNING: Connection Interrupted! >>> ' +
                            '\n\n AutoFarm has stopped!'
                    )
                    autofarm.screenshot(resource_path('resources\\AutoFarm_ScreenShot.jpg'), region=(7, 27, 1024, 768))
                    send_mail(message)

                ConIntOkX, ConIntOkY = autofarm.center(ConIntOkButton)
                autofarm.moveTo(ConIntOkX, ConIntOkY)
                wait(1)
                autofarm.click(ConIntOkX, ConIntOkY)
                print_and_log('Stopping AutoFarm bot...')
                spacer()
                wait(1)
                exit()


def starting_window(attackscript):
    print_and_log('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    print_and_log('< AutoFarm bot for Talisman Online ver.5135 by Raaski >')
    print_and_log('- - - - - - -')
    print_and_log('< Please setup config.ini correctly before starting AutoFarm >')
    print_and_log('- - - - - - -')
    print_and_log('- config.ini:')
    print_and_log('-    Class: ' + CharClass)
    print_and_log('-    FarmingSpotTimer: ' + str(FarmingSpotTimer))
    print_and_log('-    AutoPick: ' + str(AutoPick))
    print_and_log('-    SendEmail: ' + str(SendEmail))
    print_and_log('-    AutoBuff: ' + str(AutoBuff))
    print_and_log('-    SendToEmailAddress: ' + str(SendToEmailAddress))
    print_and_log('-    SendEmailAtEveryXMobKill: ' + str(SendEmailAtEveryXMobKill))
    print_and_log('-    AutobuffAtEveryXMobKill: ' + str(AutobuffAtEveryXMobKill))
    print_and_log('-    UseHpPotionPercentage: ' + str(UseHpPotionPercentage))
    print_and_log('-    UseManaPotionPercentage: ' + str(UseManaPotionPercentage))
    print_and_log('-    HpPotionQuantity: ' + str(HpPotionQuantity))
    print_and_log('-    MpPotionQuantity: ' + str(MpPotionQuantity))
    print_and_log('-    AttackScript: ' + attackscript)
    print_and_log('-    AutoBuffScript: ' + AutoBuffScript)
    print_and_log('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    print_and_log(' ')
    print_and_log('< Your char HP/MP must be full before starting the bot! >')
    print_and_log(' ')


def auto_farm(script):
    global MobCount, BattleTime, XpDifference, RunningTime

    show_char_info()

    search_target()

    BattleTimerStart = time.time()
    while True:
        get_char_info()

        if HPPercentage < 5:
            is_char_alive()

        exec(script)

        if is_enemy_dead():
            BattleTimerEnd = time.time()
            validate_lvl_up()
            print_and_log('-= [MOB KILLED] =-')
            calculate_experience_difference()
            print_and_log("Earned XP: [" + str(XpDifference) + " xp]")
            BattleTime = int((BattleTimerEnd-BattleTimerStart))
            print_and_log("Battle Lasted: [" + str(BattleTime) + " seconds]")
            spacer()
            break

        is_connection_interrupted()

    print_and_log("-= KILLED MOBS: [" + str(MobCount) + "] =-")
    print_and_log("Total XP Earned since bot started: [" + str(TotalXpEarned) + " xp]")
    RunningTime = int((BattleTimerEnd - StartingTime))
    print_and_log("AutoFarm Running time: [" + format_timespan(RunningTime) + "]")
    calculate_remaining_time_to_lvl_up()
    show_char_info()
    spacer()

    if AutoPick is True:
        get_char_info()

        if HPPercentage < UseHpPotionPercentage:
            wait(3)
            print_and_log("- < ! Danger! > -")
            print_and_log("HP < " + str(UseHpPotionPercentage) + "%")
            spacer()
            use_hp_potion()

        auto_pick()

    if AutoBuff is True:
        if MobCount % AutobuffAtEveryXMobKill == 0:
            autobuff()

    if SendEmail is True:
        if MobCount % SendEmailAtEveryXMobKill == 0:
            message = (
                '---=== CHAR INFO ===---' +
                '\nHP: [' + str(CurrentHP) + ' / ' + str(MaxHP) + '] - [' + '%.2f%%' % HPPercentage + ']' +
                '\nMP: [' + str(CurrentMana) + ' / ' + str(MaxMana) + '] - [' + '%.2f%%' % ManaPercentage + ']' +
                '\n--' +
                '\nXP: [' + str(CurrentXP) + ' / ' + str(XpToNextLvl) + '] - [' + '%.4f%%' % XpPercentage + ']' +
                '\n----------------------------------------' +
                '\n\n---=== POTIONS LEFT ===---'
                '\nHP: [' + str(HpPotionQuantity) + ']' +
                '\nMP: [' + str(MpPotionQuantity) + ']' +
                '\n----------------------------------------' +
                '\n\n---=== BATTLE INFO ===---'
                '\nMobs Killed: [' + str(MobCount) + ']' +
                '\nTotal XP earned since bot started: [' + str(TotalXpEarned) + ' xp]' +
                '\n----------------------------------------' +
                '\n\nAutoFarm running time: [' + format_timespan(RunningTime) + ']' +
                '\nApproximate time remaining to level up: [' + format_timespan(RemainingTime) + ']'
            )

            autofarm.screenshot(resource_path('resources\\AutoFarm_ScreenShot.jpg'), region=(7, 27, 1024, 768))

            send_mail(message)

    MobCount += 1


# Main Script
def main():
    global CharClass, FarmingSpotTimer, ActualXPPercentage, StartingTime, AutoPick, SendEmail
    global UseHpPotionPercentage, UseManaPotionPercentage, HpPotionQuantity, MpPotionQuantity
    global AutoBuffScript, AutobuffAtEveryXMobKill, SendEmailAtEveryXMobKill, AutoBuff, SendToEmailAddress

    # Engine Variables Setup
    CharClass = config['char']['Class']
    FarmingSpotTimer = config['auto-revive'].getint('FarmingSpotTimer')
    AutoPick = config['features'].getboolean('AutoPick')
    SendEmail = config['features'].getboolean('SendEmail')
    AutoBuff = config['features'].getboolean('AutoBuff')
    SendToEmailAddress = config['features-values']['SendToEmailAddress']
    SendEmailAtEveryXMobKill = config['features-values'].getint('SendEmailAtEveryXMobKill')
    AutobuffAtEveryXMobKill = config['features-values'].getint('AutoBuffAtEveryXMobKill')
    UseHpPotionPercentage = config['potions'].getint('UseHpPotionPercentage')
    UseManaPotionPercentage = config['potions'].getint('UseManaPotionPercentage')
    HpPotionQuantity = config['potions'].getint('HpPotionQuantity')
    MpPotionQuantity = config['potions'].getint('MpPotionQuantity')
    AttackScript = config['scripts']['AttackScript']
    AutoBuffScript = config['scripts']['AutoBuffScript']

    starting_window(AttackScript)

    # Set character actual percentage with a dot. e.g.: 40.1545
    ActualXPPercentage = float(input("Insert your actual XP percentage (e.g.: 40.1546): "))

    # Initialize Engine
    # Calculate XP to next level
    calculate_initial_experience()
    # Initialize Max HP/MP (CHAR HP/MP MUST BE FULL!)
    set_maximum_hp_mp()
    # Countdown from 3 to 1 to select Talisman Online window.
    starting_announcement()
    # Time measurement
    StartingTime = time.time()

    while True:
        auto_farm(AttackScript)


# Run AutoFarm Bot
main()
