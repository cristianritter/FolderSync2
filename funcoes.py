
def send_status_metric():
    while 1:
        update_logs()
        time.sleep(int(configs['ZABBIX']['send_metrics_interval']))
        global metric_value
        global frame
        value = metric_value
        if (value != 0):
            frame.set_error_led()

        '''
        Envia metricas para zabbix:
            ---Em caso de erro de sinc -> envia str com caminho do diretório que ocorreu o erro [strlen > 1]
            ---Em caso de sucesso nas rotinas -> envia flag str com '0' [strlen == 1]
            ---Após sincronizar todas as pastas da lista envia flag str com '1' [strlen == 1]
        '''
        try:
            packet = [
                ZabbixMetric(configs['ZABBIX']['hostname'], configs['ZABBIX']['key'], value)
            ]
            ZabbixSender(zabbix_server=configs['ZABBIX']['zabbix_server'], zabbix_port=int(configs['ZABBIX']['port'])).send(packet)
        except Exception as err:
            adiciona_linha_log("Falha de conexão com o Zabbix - "+str(err))


def adiciona_linha_log(texto):
    dataFormatada = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    mes_ano = datetime.now().strftime('_%Y%m')
    print(dataFormatada, texto)
    try:
        log_file = 'log'+mes_ano+'.txt'
        log_path = os.path.join(ROOT_DIR, 'logs')
        log_pathfile = (os.path.join(log_path, log_file))
        if (not os.path.exists(log_path)):
            os.mkdir(log_path)
        f = open(log_pathfile, "a")
        f.write(dataFormatada + ' ' + texto +"\n")
        f.close()
    except Exception as err:
        print(dataFormatada, err)
        global frame
        frame.set_error_led()
    update_logs()

def update_logs():
    global updating_logs
    if updating_logs:
        return
    updating_logs = True
    global frame
    mes_ano = datetime.now().strftime('_%Y%m')
    log_file = 'log'+mes_ano+'.txt'
    log_pathfile = os.path.join(ROOT_DIR, 'logs', log_file)
    if not os.path.exists(log_pathfile):
        updating_logs = False
        return
    f = open(log_pathfile, "r")
    linhas = f.readlines(20000000)
    linhas.reverse()
    remover=[]
    if (frame.cb1.GetValue() == False):
        for item in linhas:
            if ('<' in item):
                remover.append(item)
        for item in remover:
            linhas.remove(item)
    frame.logpanel.SetValue(''.join(linhas))
    updating_logs = False
        
def getfilename(filepath):
    try:
        pathlist = filepath.split('\\')
        filename = (pathlist[len(pathlist)-1]).lower()
        return (filename)
    except Exception as Err:
        adiciona_linha_log(str(Err)+'Getfilename')
        global frame
        frame.set_error_led()

def filetree(source, dest, sync_name):
    files_destination_md5=dict()
    files_source_md5=dict()
    try: 
        sync_ext = configs['SYNC_EXTENSIONS'][sync_name].lower().split(", ")
    except:
        sync_ext = []

    try:
        debug = 'scan dest'
        for e in os.scandir(dest):
            if e.is_file():
                if (not os.path.splitext(e.name)[1][1:].lower() in sync_ext) & (len(sync_ext) > 0):
                    continue
                files_destination_md5[e.name.lower()]=e.stat().st_mtime
            
        debug = 'scan source'
        for e in os.scandir(source):
            if e.is_file():
                if (not os.path.splitext(e.name)[1][1:].lower() in sync_ext) & (len(sync_ext) > 0):
                    continue
                files_source_md5[e.name.lower()]=e.stat().st_mtime
            
        files_to_remove=[]

        debug = 'remove files'
        for file in files_destination_md5:
            path_dest = os.path.join(dest, file)
            if file not in files_source_md5:
                try:
                    os.remove(path_dest)
                    adiciona_linha_log("Removido: " + str(path_dest))
                    files_to_remove.append(file)
                except Exception as ERR:
                    adiciona_linha_log("Erro ao remover arquivo." + str(ERR))
                    frame.set_error_led()

        debug = 'destination.pop'  
        for item in files_to_remove:
            files_destination_md5.pop(item)

        debug = 'copy files'
        thistime=round(time.time())
        for file in files_source_md5:
            path_source = os.path.join(source, file)
            path_dest = os.path.join(dest, file)
            if file not in files_destination_md5:
                aguarda_liberar_arquivo(path_source) #testar
                shutil.copy2(path_source, path_dest)                
                adiciona_linha_log("Copiado: " + str(path_source) + "[" + str(os.path.getsize( str(path_source) )) + "]" + " to " + str(path_dest) + "[" + str(os.path.getsize(str(path_dest) )) + "]")
            else:            
                if files_source_md5[file] != files_destination_md5[file]:
                    aguarda_liberar_arquivo(path_source) #testar
                    shutil.copy2(path_source, path_dest)
                    adiciona_linha_log("Sobrescrito: " + str(path_source) + "[" + str(os.path.getsize( str(path_source) )) + "]" + " to " + str(path_dest) + "[" + str(os.path.getsize( str(path_dest) )) + "]")
            if (round(time.time()) > ( thistime + 120) ):
                return 0   
        return 0

    except Exception as err:
        global metric_value
        metric_value = str(source) 
        adiciona_linha_log(str(err)+debug)
        return 1

def aguarda_liberar_arquivo(filepath_source):
    thistime2=round(time.time())
    in_file = None
    source_size1 = 0
    source_size2 = -1
    while in_file == None or source_size1 != source_size2:
        source_size1 = os.path.getsize( str(filepath_source) )
        time.sleep(0.02)
        source_size2 = os.path.getsize( str(filepath_source) )
        try:
            in_file = open(filepath_source, "rb") # opening for [r]eading as [b]inary
        except:
            pass
        if (round(time.time()) > ( thistime2 + 120) ):
            adiciona_linha_log("Arquivo protegido contra gravacao por mais de 120 segundos, não permitindo a cópia.")
            frame.set_error_led()
            break
    try:
        in_file.close()            
    except:
        pass

def event_operations(filepath_source, path_dest, sync_name, event):
    global frame
    global evento_acontecendo
    evento_acontecendo = True     
    global sincronizando
    while sincronizando == True:
        frame.led1.SetBackgroundColour('Yellow')
        frame.Refresh()
        time.sleep(0.1) 
    frame.led1.SetBackgroundColour('Red')
    frame.Refresh()
    try: 
        sync_ext = configs['SYNC_EXTENSIONS'][sync_name].lower().split(", ")
    except:
        sync_ext = []
    try:
        filename = getfilename(filepath_source).lower()
        filepath_dest = os.path.join(path_dest, filename)
        if os.path.isfile(filepath_source) or os.path.isfile(filepath_dest):
            if (os.path.splitext(filename)[1][1:].lower() in sync_ext) or (len(sync_ext) == 0):    
                if not os.path.exists(filepath_source):
                    try:
                        os.remove(filepath_dest)
                        adiciona_linha_log("Removido: " + str(filepath_dest))
                    except Exception as err:
                        adiciona_linha_log(str(err) + "Erro ao remover arquivo. " + str(filepath_dest))
                        frame.set_error_led()       
                elif not os.path.exists(filepath_dest):
                    aguarda_liberar_arquivo(filepath_source)
                    shutil.copy2(filepath_source, filepath_dest)
                    origem_size = os.path.getsize( str(filepath_source) )
                    destino_size = os.path.getsize( str(filepath_dest) )
                    adiciona_linha_log("Copiado: " + str(filepath_source) + "[" + str(origem_size) + "]" + " to " + str(filepath_dest) + "[" + str(destino_size) + "]")  
                    if (origem_size != destino_size):
                        os.remove(filepath_dest)
                        adiciona_linha_log('Cópia corrompida. Será copiado novamente no próximo sync.' + str(filepath_source))
                        frame.set_error_led()
                else:
                    source_mtime = os.stat(filepath_source).st_mtime
                    dest_mtime = os.stat(filepath_dest).st_mtime
                    if source_mtime != dest_mtime:
                        aguarda_liberar_arquivo(filepath_source)
                        shutil.copy2(filepath_source, filepath_dest)
                        origem_size = os.path.getsize( str(filepath_source) )
                        destino_size = os.path.getsize( str(filepath_dest) )
                        adiciona_linha_log("Sobrescrito: " + str(filepath_source) + "[" + str(origem_size) + "]" + " to " + str(filepath_dest) + "[" + str(destino_size) + "]")
                        if (origem_size != destino_size):
                            os.remove(filepath_dest)
                            adiciona_linha_log('Cópia corrompida. Será copiado novamente no próximo sync' + str(filepath_source)) 
                            frame.set_error_led()

        frame.led1.SetBackgroundColour('gray')
        frame.Refresh()
    except Exception as Err:
        adiciona_linha_log(str(Err)) 
        global metric_value
        metric_value = str(filepath_source)
    evento_acontecendo = False

def sync_all_folders():
    try:
        update_logs()
        error_counter = 0
        for item in configs['SYNC_FOLDERS']:
            time.sleep(0.1)
            path = (configs['SYNC_FOLDERS'][item]).split(', ')
            error_counter += filetree(path[0], path[1], item)
            time.sleep(0.1)
        if error_counter == 0:
            global metric_value
            metric_value = 0
    except Exception as err:
        adiciona_linha_log("Falha durante execução da função sync_all_folders - "+str(err))
        global frame
        frame.set_error_led()


def syncs_thread():
    while sleep_time > 0:
        global frame
        frame.led2.SetBackgroundColour('yellow')
        frame.Refresh()
        global sincronizando
        sincronizando = True
        global evento_acontecendo
        if evento_acontecendo == True:
            sincronizando = False
            time.sleep(1)
            continue
        frame.led2.SetBackgroundColour('Red')
        frame.Refresh()
        sync_all_folders()
        sincronizando = False
        frame.led2.SetBackgroundColour('gray')
        frame.Refresh()
        time.sleep(sleep_time)
