# FolderSync

![Interface do Usuário](caminho/para/imagem/interface.png)

## Descrição

O FolderSync é um gerenciador de conteúdo desenvolvido em Python para sincronizar diretórios em tempo real. Ele utiliza a biblioteca `watchdog.observers` para monitorar mudanças nas pastas, permitindo a gestão eficiente de arquivos locais ou em redes. O software foi projetado para atender às necessidades específicas do grupo NSC em Santa Catarina, gerenciando o tráfego de arquivos musicais e comerciais para rádios e emissoras de TV.

## Funcionalidades

- Sincronização em tempo real de diretórios locais e de rede.
- Tratamento de eventos, como erros de gravação, arquivos protegidos contra gravação, etc.
- Integração com a biblioteca `pyzabbix` para gerar traps e enviar alertas para um servidor Zabbix em caso de problemas na cópia de arquivos.
- Interface gráfica desenvolvida com a biblioteca `wx.python`.
- Registro detalhado de operações em arquivos de log ficam armazenados em src/logs .

## Requisitos
Python 3.x \
Bibliotecas Python: watchdog, pyzabbix, wxpython
## Instalação
Clone o repositório: 
```shel
git clone https://github.com/cristianritter/FolderSync2.git \
cd FolderSync2
```

## Crie e ative um ambiente virtual:
```shel
python -m venv venv
source venv/bin/activate   # No Windows, use `venv\Scripts\activate`
```
## Instale as dependências:
```shel
pip install -r requirements.txt
```
## Execute o programa usando o seguinte comando:
```shel
python src/main.py
``` 
A interface gráfica será iniciada, permitindo a configuração e monitoramento de diretórios.

## Configuração
Edite o arquivo de configuração config.json na pasta user do projeto com as informações necessárias.
Dúvidas sobre o arquivo de configuração podem ser discutidas por email ou por dm com o desenvolvedor.

## Contribuição
Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

## Licença
Este projeto é distribuído sob a licença {{sua_licenca}}. Consulte o arquivo LICENSE para obter mais detalhes.
## Estrutura de Pastas e Configuração

A estrutura de pastas é organizada da seguinte forma:

- `src`: Contém os arquivos de código, incluindo o arquivo `main.py`.
- `user`: Contém os arquivos de configuração do usuário. Pode se manter arquivos de config antigos na pasta, sendo que o arquivo que será utilizando pelo software será o nomeado como 'config.json'.
Segue abaixo um modelo de arquivo de configuração no formato JSON:
```json
{
    "trayicon_alias": "CBN_FLO",
    "check_all_files_interval": 300,
    "zabbix_key": "foldersync_cbnflo",
    "zabbix_instances": {
        "instance1": {
            "enabled": 1,
            "hostname": "FLS - SERVER-RADIOS",
            "server_ip": "10.51.23.101",
            "port": 10051,
            "send_metrics_interval": 30
        },
        "instance2": {
            "enabled": 0,
            "hostname": "FLS - SERVER-RADIOS",
            "server_ip": "10.51.23.103",
            "port": 10051,
            "send_metrics_interval": 30
        }
    },   
    "folders_to_sync": {
        "sync01": {
            "origem": "\\\\10.70.40.10\\Midia_plus\\CBN_FLS\\Roteiros",
            "destino": "C:\\Teste\\RadiosComercial\\CBN\\Programacao",
            "sync_extensions": ["txt", "pl1"]
        },
        "sync02": {
            "origem": "\\\\10.70.40.10\\RadiosComercial\\CBN\\Audio",
            "destino": "C:\\Teste\\RadiosComercial\\CBN\\Audio",
            "sync_extensions": ["mp3", "wav"]
        }
    }
}

```


