#!/usr/bin/python3

'''
This file is part of the remote_rsync project (https://github.com/libicocco/remote_rsync).

    Copyright(c) 2011 Javier Romero
    * jrgn AT kth DOT se

    remote_rsync is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    remote_rsync is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with remote_rsync.  If not, see <http://www.gnu.org/licenses/>.
'''

import subprocess,os,re,socket,datetime,sys,getopt

def rotate(dataDestinationPath,serverURL,sshCommand):
  nDailySnapshots=4
  nWeeklySnapshots=4
  nMonthlySnapshots=4
  # get the list of snapshots
  snapshots=subprocess.check_output(sshCommand+
      [serverURL,'ls '+dataDestinationPath]).decode('utf-8').split('\n')
  
  # get the daily snapshots; if there are more than allowed either remove the oldest or move it to weekly
  dailySnapshots=list(filter(lambda s:s.startswith('daily_'),snapshots))
  dailySnapshots.sort()
  dailySnapshots=list(map(lambda s:os.path.join(dataDestinationPath,s),dailySnapshots))
  if len(dailySnapshots)>nDailySnapshots:
      if datetime.datetime.now().weekday()==3: # save weekly snapshot on thursdays
          subprocess.call(sshCommand+[serverURL,
              'mv '+dailySnapshots[0]+' '+os.path.join(dataDestinationPath,'weekly_'+date)])
      else:
          subprocess.call(sshCommand+[serverURL,'rm -rf '+dailySnapshots[0]])
  
  # get the weekly snapshots; if there are more than allowed either remove the oldest or move it to monthly
  weeklySnapshots=list(filter(lambda s:s.startswith('weekly_'),snapshots))
  weeklySnapshots.sort()
  weeklySnapshots=list(map(lambda s:os.path.join(dataDestinationPath,s),weeklySnapshots))
  if len(weeklySnapshots)>(nWeeklySnapshots-1): # -1 because the previous have added one after the list creation
      if datetime.datetime.now().day==20: # save monthly snapshot on the 20th
          subprocess.call(sshCommand+[serverURL,
              'mv '+weeklySnapshots[0]+' '+os.path.join(dataDestinationPath,'monthly_'+date)])
      else:
          subprocess.call(sshCommand+[serverURL,'rm -rf '+weeklySnapshots[0]])
  
  # get the monthly snapshots; if there are more than allowed remove the oldest
  monthlySnapshots=list(filter(lambda s:s.startswith('monthly_'),snapshots))
  monthlySnapshots.sort()
  monthlySnapshots=list(map(lambda s:os.path.join(dataDestinationPath,s),monthlySnapshots))
  if len(monthlySnapshots)>(nMonthlySnapshots-1): # -1 because the previous have added one after the list creation
          subprocess.call(sshCommand+[serverURL,'rm -rf '+monthlySnapshots[0]])

def getNoBackupRules(dataSourcePath):
  if os.getuid() == 0:# if superuser is available, get the nobackup files with locate
    # updatedb in case somebody created a .nobackup
    subprocess.call(['/usr/bin/updatedb']) # needs sudo
    # create an excluding rule for each .nobackup
    nobackuprules=(subprocess.check_output(["/usr/bin/locate",".nobackup"])).decode("utf-8").split('\n')[:-1]
  else: # if not, get them with find
    # create an excluding rule for each .nobackup
    nobackuprules=(subprocess.check_output(["/usr/bin/find",dataSourcePath,"-name",".nobackup"])).decode("utf-8").split('\n')[:-1]

  nobackuprules=list(map(lambda s:os.path.dirname(s),nobackuprules))
  nobackuprules=list(map(lambda s:re.sub(r'^.*%s'%dataSourcePath,r'',s),nobackuprules))
  nobackuprules=list(map(lambda s:re.sub(r'(.*)',r'--exclude=\1/***',s),nobackuprules))
  return nobackuprules

def backup(dataSourcePath,serverURL,sshCommand,excludesFile):
  dataDestinationPath=socket.gethostname()
  # exclude directories with .nobackup file inside
  nobackuprules = getNoBackupRules(dataSourcePath)
  
  # get time
  date=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
  
  # create backup folder if not created yet
  subprocess.call(sshCommand+[serverURL,'mkdir -p '+dataDestinationPath])

  currentLink='current'
  currentLinkPath=os.path.join(dataDestinationPath,currentLink)
  incompletePath=os.path.join(dataDestinationPath,'incomplete_'+date)
  # completePath has to be absolute for the ln -s
  completePath=os.path.join('~/',dataDestinationPath,'daily_'+date)
  # rsync linking against latest backup (currentLinkPath),
  # excluding folders with .nobackup file inside
  # and patterns in excludesFile
  subprocess.call(['/usr/bin/rsync',
                   '-a', # could try -az
                   '--progress', # progress dialog; remove this option if run with cron
                   '--delete',
                   '--delete-excluded',
                   '--link-dest=../'+currentLink,
                   '-e',
                   ' '.join(sshCommand)]+
                   nobackuprules+ # looks like nobackuprules should precede the excludesFile 
                   ['--exclude-from='+excludesFile,
                     dataSourcePath,
                     serverURL+':'+incompletePath])
  
  # set the backup as complete and update the current link
  subprocess.call(sshCommand+[serverURL,
  'mv '+incompletePath+' '+completePath+' && rm -f '+currentLinkPath+' && '+ 'ln -s '+completePath+' '+currentLinkPath])
  rotate(dataDestinationPath,serverURL,sshCommand)

def usage():
  print("usage: ",sys.argv[0]," [-s user@server] | [-d data to be backed up] | [-k ssh key path]")
  print("-s: URL to the path where you want to backup your data")
  print("-d: Path to the local data to be backed up")
  print("-k: Path to local ssh key (http://www.thegeekstuff.com/2008/11/3-steps-to-perform-ssh-login-without-password-using-ssh-keygen-ssh-copy-id/)")
  sys.exit(2)

def main(argv):                         
  # default values for the options; can be changed if somebody wants to call the script without options
  serverURL = 'user@remote-host'
  dataSourcePath=sys.path[0]
  sshKeyPath = ''
  excludesFile=''
  try:                                
    opts, args = getopt.getopt(argv, "hs:d:k:e:", ["help", "server_url=","data_path=","ssh_key_path=","exclude_file="]) 
  except getopt.GetoptError:           
    usage()                          
    sys.exit(2)    
  for opt, arg in opts:                
    if opt in ("-h", "--help"):      
      usage()                     
      sys.exit()                  
    elif opt in ("-s", "--server_url"): 
      serverURL = arg               
    elif opt in ("-d", "--data_path"): 
      dataSourcePath = arg               
    elif opt in ("-k", "--ssh_key_path"): 
      sshKeyPath = arg               
    elif opt in ("-e", "--exclude_file"): 
      excludesFile = arg               

  if not os.path.isfile(sshKeyPath):
    print('SSH key path ' + sshKeyPath + ' is not a file; you will be requested a password (several times)')
    sshCommand = ['/usr/bin/ssh']
  else:
    sshCommand = ['/usr/bin/ssh','-i',sshKeyPath]

  if not os.path.isdir(dataSourcePath):
    print('Data source path ' + sshKeyPath + ' is not a proper path')

  if not os.path.isfile(excludesFile):
    excludesFile=''

  backup(dataSourcePath,serverURL,sshCommand,excludesFile)

if __name__=="__main__":
  main(sys.argv[1:])
