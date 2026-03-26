import json
from urllib.parse import parse_qs, parse_qsl

from asgiref.sync import async_to_sync
from channels.consumer import SyncConsumer
from channels.exceptions import StopConsumer

from user.jwt_utils import decode_jwt_token
from user.models import CustomUser
from user.serializers import IotDataSerializer


class IotIngestConsumer(SyncConsumer):
    '''
    Websocket endpoint for data ingestion
    '''
    def websocket_connect(self, event):
        print(event)
        headers = dict(self.scope['headers'])
        auth_token = headers.get(b'token', b'').decode('utf-8')
        user = decode_jwt_token(auth_token)
        if user is None:
            self.send({
                'type': 'websocket.close'
            })
        else:
            self.send({
                'type': 'websocket.accept'
            })

    def websocket_receive(self, event):
        print('message', event)
        headers = dict(self.scope['headers'])
        auth_token = headers.get(b'token', b'').decode('utf-8')
        user = decode_jwt_token(auth_token)
        if user is None:
            self.send({
                'type': 'websocket.close'
            })
        else:
            data = json.loads(event['text'])
            serializer = IotDataSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                self.send({
                    'type': 'websocket.send',
                    'text': json.dumps({'message': 'Data saved successfully'})
                })
                async_to_sync(self.channel_layer.group_send)(
                    f"user_{serializer.data['user_id']}",
                    {
                        'type': 'chat.message',
                        'message': json.dumps({'event': 'NEW_DATA', 'data': serializer.data})
                    }
                )

            else:
                print('Invalid data', serializer.errors)
                self.send({
                    'type': 'websocket.send',
                    'text': json.dumps({'error': 'Invalid data', 'details': serializer.errors})
                })

    def chat_message(self, event):
        print('message', event)
        self.send({
            'type': 'websocket.send',
            'text': event['message']
        })

    def websocket_disconnect(self, event):
        print('disconnected', event)
        # async_to_sync(self.channel_layer.group_discard)('test_group', self.channel_name)
        raise StopConsumer()


class SubscribeConsumer(SyncConsumer):
    '''
    Websocket endpoint for subscribe user data based on user_id
    '''
    def __init__(self):
        super().__init__()
        self.group_name = None

    def websocket_connect(self, event):
        print(event)
        headers = dict(self.scope['headers'])
        auth_token = headers.get(b'token', b'').decode('utf-8')
        user = decode_jwt_token(auth_token)
        if user is None:
            self.send({
                'type': 'websocket.close'
            })
        else:
            query_string = self.scope.get('query_string', b'').decode('utf-8')
            query_params = dict(parse_qsl(query_string))
            if query_params.get('user_id'):
                user_id = query_params['user_id']
                user = CustomUser.objects.filter(user_id=user_id).first()
                if user:
                    self.group_name = f'user_{user_id}'
                    async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
                    self.send({
                        'type': 'websocket.accept'
                    })
                else:
                    self.send({
                        'type': 'websocket.accept'
                    })
                    self.send({
                        'type': 'websocket.send',
                        'text': 'Invalid User ID!'
                    })
                    self.send({
                        'type': 'websocket.close'
                    })
            else:
                self.send({
                    'type': 'websocket.close'
                })

    def websocket_receive(self, event):
        print('message', event)

    def websocket_disconnect(self, event):
        print('disconnected', event)
        raise StopConsumer()

    def chat_message(self, event):
        print('message', event)
        self.send({
            'type': 'websocket.send',
            'text': event['message']
        })
