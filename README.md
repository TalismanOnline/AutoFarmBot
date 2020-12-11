# AutoFarmBot
Talisman Online AutoFarm Bot project

1 - Before starting Auto Farm bot, you need to setup the config.ini accordingly to your character's info (if it is a Mage or a Fighter, how many HP/MP Potions you have, if you want AutoPick/SendEmail features to be on, etc).

2 - EVERYTIME YOU START THE BOT, YOU NEED TO SET YOUR ACTUAL XP PERCENTAGE FOR CALCULATIONS!!!

3 - SendEmail feature: AutoFarm already have its own email configuration for sending you the updates. You just have to set YOUR desired e-mail to receive the updates (you don't need to set any password). 
Updates are: 
	- Every x Mob Kill (set in config.ini)
	- Char's death
	- Level Up
	- Connection Interrupted

4 - Auto-Revive feature needs a "Star Path" (Auto-Path - "right click") set on your map (and your Mount set to 0 on the skill bar), and the FarmingSpotTimer needs to be calculated like this: go to the respawn point in the village/city, evoke your Mount, set the auto-path to the desired farming location and start counting the seconds it take to go there. (e.g. in MDV: your respawn point is near Blacksmith. If you set the Auto-Path to the Deers location, it will take like 10 seconds on a +6 mount. So you should set FarmingSpotTimer = 10 in config.ini.)

5 - AutoPick feature is not 10/10. It's more likely to be 8/10. But it can be very, very useful for those who don't have a pet with AutoPick.

6 - All your battle info will be stored on "log" folder. You can see if anything went wrong.

7 - HP/MP/XP and Mob Selected/Mob HP are infos from the game memory address. If it's not working correctly, the game propably updated. AutoPick/UsePotion/ConnectionInterrupted etc is image recognition.

8 - Set your HP/MP Potions on your shortcut bar, AutoFarm needs to see it to use it.

9 - Actual working version of Talisman Online is ver.5135!

10 - To stop AutoFarm, just close its window or select it and press Ctrl + C.

11 - AutoFarm works better in resolution 1024x768 (heh, sorry). Just set it in Talisman Online -> System -> Graphics -> Screen Size = 1024x768.

11 - Enjoy! :-)

Regards, Raaski.
