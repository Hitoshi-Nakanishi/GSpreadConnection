import re, string
import numpy as np
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials as SAC

class GSpreadConnection:
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    def __init__(self,cred_json_path):
        self.cred_json_path = cred_json_path
        self.sh = None
    
    def connect(self):
        credentials = SAC.from_json_keyfile_name(self.cred_json_path, GSpreadConnection.scope)
        self.gc = gspread.authorize(credentials)
        return(self)
    
    def open_sheet(self, filename):
        self.sh = self.gc.open(filename)
        return(self)
    
    def create_sheet(self, filename, shared_user='MyGmail'):
        self.sh = self.gc.create(filename)
        if shared_user is not 'MyGmail':
            self.sh.share(shared_user, perm_type='user', role='writer')
        return(self)
    
    def load_titles(self):
        if self.sh is None: return(self)
        self.titlelist = list(map(lambda wsh: wsh.title, self.sh.worksheets()))
        print(self.titlelist)
        return(self)
    
    def read_as_pandas(self, sheetname):
        worksheet = self.sh.worksheet(sheetname)
        df = pd.DataFrame(worksheet.get_all_values())
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        self.df = df.apply(lambda x: x.str.replace(",","")).apply(pd.to_numeric, errors='ignore')
        return(self)
    
    def upload_from_pandas(self, sheetname, df, pos = 'A1'):
        len_c, len_r = df.shape[1], df.shape[0]

        def n2let(num):
            letters = ''
            while num:
                mod = (num - 1) % 26
                letters += chr(mod + 65)
                num = (num - 1) // 26
            return(''.join(reversed(letters)))

        def let2n(let):
            num = 0
            for l in let:
                if l in string.ascii_letters:
                    num = num * 26 + (ord(l.upper()) - ord('A')) + 1
            return(num)

        def strip_let(pos):
            return(int(re.sub("\D", "", pos)))
        
        wsh = self.sh.worksheet(sheetname)
        cell_list = wsh.range(pos+":"+n2let(let2n(pos)+len_c-1)+str(strip_let(pos)+len_r-1))
        cell_list = np.array(cell_list).reshape(len_r,len_c)
        for (x,y), cell in np.ndenumerate(cell_list):
            cell.value = df.iat[x,y]
        cell_list = cell_list.flatten().tolist()
        wsh.update_cells(cell_list)
        return(self)
