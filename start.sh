rm romwhist.log
#gunicorn --env SCRIPT_NAME=/cards -k eventlet -w 1 -b :5000 romwhist:'create_app()'
gunicorn -k eventlet -w 1 -b :5000 romwhist:'create_app()'
