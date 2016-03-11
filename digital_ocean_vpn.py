import requests
import json
import time
import argparse
import ConfigParser
import sys

class Api:

    def __init__(self, conf_file='conf.cfg'):
        config = ConfigParser.ConfigParser()
        config.readfp(open(conf_file))
        token = config.get('auth', 'token')
        self.auth_headers = {'Authorization': 'Bearer {}'.format(token),
                             'Content-Type': 'application/json'}
        self.droplet_data = dict(config.items('droplet'))

    def droplets(self):
        response = requests.get(url='https://api.digitalocean.com/v2/droplets', headers=self.auth_headers)
        return json.loads(response.text)

    def images(self):
        response = requests.get(url='https://api.digitalocean.com/v2/images?private=true', headers=self.auth_headers)
        return json.loads(response.text)

    def available_regions(self):
        response = requests.get(url='https://api.digitalocean.com/v2/regions?available=true', headers=self.auth_headers)
        regions = {'regions': []}
        for region in json.loads(response.text)['regions']:
            if region['available']:
                regions['regions'].append(region)
        return regions

    def create_droplet(self):
        response = requests.post(url='https://api.digitalocean.com/v2/droplets', headers=self.auth_headers,
                                 data=json.dumps(self.droplet_data))
        return json.loads(response.text)

    def delete_droplet(self, id):
        requests.delete(url='https://api.digitalocean.com/v2/droplets/{}'.format(id), headers=self.auth_headers)

    def id_droplet(self):
        response = requests.get(url='https://api.digitalocean.com/v2/droplets', headers=self.auth_headers)
        droplets = json.loads(response.text)
        if droplets['droplets']:
            if len(droplets['droplets']) > 1:
                print 'You have more than one droplet'
            return droplets['droplets'][0]['id']
        else:
            return None

    def droplet(self, droplet_id):
        response = requests.get(url='https://api.digitalocean.com/v2/droplets/{}'.format(droplet_id), headers=self.auth_headers)
        return json.loads(response.text)

    def power_off(self, droplet_id):
        response = requests.post(url='https://api.digitalocean.com/v2/droplets/{}/actions'.format(droplet_id),
                                 headers=self.auth_headers, data='{"type":"power_off"}')
        return json.loads(response.text)

    def check_action(self, droplet_id, action_id):
        response = requests.get(url='https://api.digitalocean.com/v2/droplets/{}/actions/{}'.format(droplet_id, action_id),
                                headers=self.auth_headers)
        action = json.loads(response.text)
        return action['action']['status']

    def shutdown(self):
        droplet_id = self.id_droplet()
        _droplet = self.droplet(droplet_id)['droplet']
        if _droplet['status'] != 'off':
            stop_action_id = self.power_off(droplet_id)['action']['id']
            stop_action_status = self.check_action(droplet_id, stop_action_id)
            i = 0
            while stop_action_status != 'completed':
                message = "{} {}{}".format('Stopping:', stop_action_status, '.' * (i & 3))
                sys.stdout.write(message)
                sys.stdout.flush()
                sys.stdout.write('\b' * len(message))
                time.sleep(0.5)
                stop_action_status = self.check_action(droplet_id, stop_action_id)
                i += 1
            sys.stdout.flush()
            sys.stdout.write('\b' * len(message))
            print("Stopped")
        self.delete_droplet(droplet_id)
        print 'Dropped'

    def start_droplet(self):
        droplet_id = self.create_droplet()['droplet']['id']
        droplet_status = self.droplet(droplet_id)['droplet']['status']
        i = 0
        while droplet_status != 'active':
            message = '{} {}{}'.format('Starting:', droplet_status, '.' * (i & 3))
            sys.stdout.write(message)
            sys.stdout.flush()
            sys.stdout.write('\b' * len(message))
            time.sleep(0.5)
            i += 1
            droplet_status = self.droplet(droplet_id)['droplet']['status']
        sys.stdout.flush()
        sys.stdout.write('\b' * len(message))
        print("Started")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--status', action='store_true', dest='status', default=False)
    parser.add_argument('--run', action='store_true', dest='run', default=False)
    parser.add_argument('--drop', action='store_true', dest='drop', default=False)
    parser.add_argument('--images', action='store_true', dest='images', default=False)

    args = parser.parse_args()
    api = Api()
    if args.status:
        droplet_id = api.id_droplet()
        if droplet_id:
            _droplet = api.droplet(droplet_id)['droplet']
            print 'droplet: {}, status:{}, ip:{}'.format(_droplet['name'], _droplet['status'], _droplet['networks']['v4'][0]['ip_address'])
        else:
            print 'No droplets'
    if args.run:
        api.start_droplet()
    if args.drop:
        api.shutdown()
    if args.images:
        print api.images()
