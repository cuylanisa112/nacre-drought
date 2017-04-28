import requests
import sqlite3
# from time import sleep
# import sys

conn = sqlite3.connect('dpt.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS pemilih (
    id INTEGER NOT NULL,
    nama VARCHAR(100) NOT NULL,
    nik VARCHAR(20) NOT NULL,
    putaran INTEGER NOT NULL,
    jenisKelaminId INTEGER NOT NULL,
    tempatLahirId INTEGER NOT NULL,
    tpsId INTEGER NOT NULL,
    UNIQUE (id, nama, putaran, jenisKelaminId, tempatLahirId, tpsId),
    FOREIGN KEY (jenisKelaminId) REFERENCES jenisKelamin(id),
    FOREIGN KEY (tempatLahirId) REFERENCES tempatLahir(id),
    FOREIGN KEY (tpsId) REFERENCES tps(id)
)''')
c.execute('''CREATE TABLE IF NOT EXISTS jenisKelamin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama VARCHAR(100) NOT NULL UNIQUE
)''')

try:
    c.executemany('INSERT INTO jenisKelamin (nama) VALUES (?)', (('laki-laki',), ('perempuan',)))
except sqlite3.IntegrityError:
    pass

c.execute('''CREATE TABLE IF NOT EXISTS tempatLahir (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nama varchar(100) NOT NULL UNIQUE
)''')


rowTempatLahir = c.execute('SELECT id,nama FROM tempatLahir').fetchall()
def getTempatLahirId(tempatLahirPemilih):
    global rowTempatLahir
    try:
        tempatLahirId = tuple( r[0] for r in rowTempatLahir if tempatLahirPemilih.upper() == r[1])[0]
    except IndexError:
        tempatLahirId = c.execute( 'INSERT INTO tempatLahir (nama) VALUES (?)', (tempatLahirPemilih.upper(),)).lastrowid
        rowTempatLahir = c.execute( 'SELECT id,nama FROM tempatLahir').fetchall()

    return tempatLahirId


rowKelurahan = c.execute('SELECT id,nama FROM kelurahan').fetchall()
rowTps = c.execute('SELECT id,nama,kelurahanId FROM tps').fetchall()
def getTpsId(url):
    location = url.split('/')
    kelurahanId = tuple(r[0] for r in rowKelurahan if location[-3].upper() == r[1])[0]
    tpsId = tuple(r[0] for r in rowTps if int(location[-2]) == r[1] and kelurahanId == r[2])[0]

    return tpsId


rowJenisKelamin = c.execute('SELECT id,nama FROM jenisKelamin').fetchall()
def preparePemilih(pemilih, tpsId):
    jenisKelaminId = tuple(r[0] for r in rowJenisKelamin if pemilih[ 'jenisKelamin'].lower() == r[1])[0]
    tempatLahirId = 1 if not pemilih['tempatLahir'] else getTempatLahirId(pemilih['tempatLahir'])

    return (pemilih['id'], pemilih['nama'].upper(), pemilih['nik'], int(pemilih['putaran']), jenisKelaminId, tempatLahirId, tpsId,)


data = []
dataCheckExist = set(r[0] for r in c.execute('SELECT id FROM pemilih').fetchall())
urlData = set(r[0] for r in c.execute( 'SELECT url FROM _source WHERE isFetched=0').fetchall())
try:
    for urlVal in urlData:
        tps = requests.get(url=urlVal).json()['data']
        tpsId = getTpsId(urlVal.replace('%20', ' '))

        for pemilih in tps:
            if pemilih['id'] in dataCheckExist:
                # print('Pemilih {nik} {nama} already exists'.format( nik=pemilih['nik'], nama=pemilih['nama']))
                pass
            else:
                # print('Append {nik} {nama} to data pemilih'.format( nik=pemilih['nik'], nama=pemilih['nama']))
                print(pemilih)
                pemilih = preparePemilih(pemilih, tpsId)

                data.append(pemilih)

        print('removing {url} from list'.format(url=urlVal))
        c.execute('UPDATE _source set isFetched=1 where url=?', (urlVal,))
except KeyboardInterrupt:
    pass
finally:
    print('saving pemilih to database')

    c.executemany('''INSERT INTO
        pemilih (id, nama, nik, putaran, jenisKelaminId, tempatLahirId, tpsId)
        VALUES  ( ?,    ?,   ?,       ?,              ?,             ?,     ?)''', tuple(data))
    conn.commit()
    conn.close()
