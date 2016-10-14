import argparse
import mechanize
import cookielib
import fileinput
import getpass
from datetime import date

def parse_arguments():
    parser = argparse.ArgumentParser(description='Add geocaching.com pocket queries by date range')
    
    parser.add_argument('-u', '--username', help='Your geocaching.com username', required=True)
    parser.add_argument('-p', '--prefix', help='A string to prefix each query name', default='pq-')
    parser.add_argument('-s', '--state', help='The geocaching.com state_id. NSW=52, VIC=53, QLD=54, SA=55, WA=56, TAS=57, NT=58, ACT=59', required=True)
    parser.add_argument('-e', '--email', help='The email address to receive notifications. Omit to use default', default=None)
    parser.add_argument('-f', '--datafile', help='The file containing the date ranges. Default=standard input', default='-')

    return parser.parse_args()

def gc_session(username, password):
    # Create a browser
    br = mechanize.Browser()

    # Add a Cookie Jar
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)

    # Set Browser options
    br.set_handle_equiv(True)
    #br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)

    # Follows refresh 0 but not hangs on refresh > 0
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    # Want debugging messages?
    #br.set_debug_http(True)
    #br.set_debug_redirects(True)
    #br.set_debug_responses(True)

    # Set a User-Agent
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    # Open the login page
    r = br.open('https://www.geocaching.com/login/default.aspx')
    if r.code != 200:
        raise ValueError("Unable to open login page")

    # Find the login form
    for f in br.forms():
        if f.attrs['id'] == 'aspnetForm':
            br.form = f
            break
    if br.form == None:
        raise ValueError("Login form not found")

    br.form['ctl00$ContentBody$tbUsername'] = username
    br.form['ctl00$ContentBody$tbPassword'] = password

    r = br.submit()
    if r.code != 200:
        raise ValueError("Failed to submit login details")

    return br


def add_pq(session,name,state_id,start_day,start_month,start_year,end_day,end_month,end_year,email=None):
    r = session.open('https://www.geocaching.com/pocket/gcquery.aspx')

    for f in session.forms():
        if f.attrs.get('id') == 'aspnetForm':
            session.form = f
            break
    if session.form == None:
        raise ValueError("Pocket query form not found")

    session.form['ctl00$ContentBody$rbRunOption']         = ['2']     # 1 = run and deselect, 2 = run weekly, 3 = run once and delete
    session.form['ctl00$ContentBody$tbName']              = name

    session.form['ctl00$ContentBody$tbResults']           = '1000'
    session.form['ctl00$ContentBody$CountryState']        = ['rbStates']
    session.form['ctl00$ContentBody$lbStates']            = [state_id]
    session.form['ctl00$ContentBody$Placed']              = ['rbPlacedBetween']

    session.form['ctl00$ContentBody$DateTimeBegin$Day']   = [start_day]
    session.form['ctl00$ContentBody$DateTimeBegin$Month'] = [start_month]
    session.form['ctl00$ContentBody$DateTimeBegin$Year']  = [start_year]

    session.form['ctl00$ContentBody$DateTimeEnd$Day']     = [end_day]
    session.form['ctl00$ContentBody$DateTimeEnd$Month']   = [end_month]
    session.form['ctl00$ContentBody$DateTimeEnd$Year']    = [end_year]

    if email != None:
        session.form['ctl00$ContentBody$ddlAltEmails']        = [email]
    session.form['ctl00$ContentBody$cbIncludePQNameInFileName'] = ['on']

    r = session.submit()
    if r.code != 200:
        raise ValueError("Failed to submit pocket query details")



# Lookup month name
def month_num(month_name):
    return ['January','February','March','April','May','June','July','August','September','October','November','December'].index(month_name)+1

# Convert project-gc date to pq form date
def pgcdate_split(pgcdate):
    (m,d,y) = pgcdate.rstrip().split("/")
    mm = str(month_num(m))
    dd = str(d).lstrip("0")              # Can't have leading zero in pq form
    return (dd,mm,y)

args = parse_arguments()
    
s = gc_session(args.username, getpass.getpass('Password: '))

for line in fileinput.input([args.datafile]):
   (row,start_date,end_date,num_days,num_caches) = line.rstrip().split("\t")
   print "Adding row "+row
   (start_day, start_month, start_year) = pgcdate_split(start_date)
   if end_date == "":                    # The last entry has no end date. Use end of next year
       end_day = '31'
       end_month = '12'
       end_year = str(date.today().year + 1)
   else:
      (end_day, end_month, end_year) = pgcdate_split(end_date)

   add_pq(s,args.prefix+row.zfill(2),args.state,start_day,start_month,start_year,end_day,end_month,end_year,args.email)

fileinput.close()