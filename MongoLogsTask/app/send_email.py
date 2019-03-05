from packages.core.messercore.container import ContainerApp
import re
import os
import sys
import pandas as pd
import jinja2

app = ContainerApp(__name__)


def process_log_rank(file_name, region):
    file = open(path+'/'+file_name, 'r', encoding='utf-8')
    file_list = list(file)
    keyword = file_list.index('QUERIES\n')
    del file_list[0:keyword+1]
    for i, v in enumerate(file_list):
        if v == 'no queries found.\n':
            del file_list[i]
            df_empty = pd.DataFrame()
            return df_empty
        else:
            table = []
            for line in file_list[2:-1]:
                table.append(re.split(r'\s{2,}', line[:-1]))
            df = pd.DataFrame(table, columns=re.split(
                r'\s{2,}', (file_list[0])[:-1]))
            df['region'] = region
            df.iloc[:, 6:8] = (df.iloc[:, 6:8]).astype(float).round(2)
            return df


if __name__ == '__main__':
    path = '/app/output'
    region = sys.argv[1]
    files = os.listdir(path)
    context = pd.DataFrame()
    for file_name in files:
        df = process_log_rank(file_name, region)
        context = context.append(df)
    try:
        records = context.to_dict('records')
        template_loader = jinja2.FileSystemLoader(searchpath='./templates')
        template_env = jinja2.Environment(loader=template_loader)
        TEMPLATE_FILE = 'log_summary.html'
        template = template_env.get_template(TEMPLATE_FILE)
        html = template.render(records=records)
        email_to = app.get_env('EMAIL')
        app.send_email('reports@messerfs.com', email_to.split(';'),
                       'Daily log report',
                       body_html=html)
    except Exception:
        app.logger.exception('Failed to email')