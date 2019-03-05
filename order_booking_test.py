import json
import os

from packages.core.messercore.utils import get_datacube
from packages.core.messercore.container import ContainerApp
app = ContainerApp(__name__)
dc = get_datacube(app)


def main():
    test_case_dir = 'test_cases/'
    for tcd in os.listdir(test_case_dir):
        order_new_dir = test_case_dir + tcd + '/' + tcd + '.txt'
        order_new = open(order_new_dir).read()
        if order_new != '':
            order_new_json = json.loads(order_new)
            order_new_json['Extended']['TestId'] = tcd
            order_new_info = dc.order.post(order_new_json)
            app.logger.info(
                'New test case {} successfully.'.format(tcd))
            order_fill_dir = test_case_dir + tcd + '/' + tcd + 'f.txt'
            order_fill = open(order_fill_dir).read()
            if order_fill != '':
                order_fill_json = json.loads(order_fill)
                order_fill_json['Id'] = order_new_info['RequestId']
                dc.order.fill(order_fill_json)
                app.logger.info(
                    'Fill test case {} successfully.'.format(tcd))
            else:
                app.logger.info(
                    'Test case {} fill is empty, please check.'.format(tcd))
                continue
        else:
            app.logger.info(
                'Test case {} new is empty, please check.'.format(tcd))
            continue


if __name__ == '__main__':
    app.start(main)