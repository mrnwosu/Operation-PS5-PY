# In[ ]:
import os

def playSound():
    print('Playing Sound.')
    try:
        wd = os.getcwd()
        print(wd)
        NOTIFICATION_FILE_PATH = f'{wd}\\assets\\youGotmail.wav'
        command = f'powershell -c (New-Object Media.SoundPlayer "{NOTIFICATION_FILE_PATH}").PlaySync()'
        os.system(command)
    except:
        print('Something wrong happened when playing sound')
# %%
