from datetime import *

from flask import Blueprint, request, jsonify, abort, url_for, make_response
from flask_cors import CORS
from flask_caching import Cache

from kubernetes import client, config

try:
    config.load_kube_config()
except:
    config.load_incluster_config()
kube = client.CoreV1Api()

parent_app = None
api = Blueprint('api', __name__)
CORS(api)

cache = Cache()

def mk_dt(dt):
    if isinstance(dt, timedelta):
        tsec = dt.total_seconds()
    else:
        tsec = dt
    times = []
    
    tsec = int(tsec)
    def unit(ivl, what):
        nonlocal tsec
        if tsec > ivl:
            times.append(f"{tsec//ivl}{what}")
        tsec %= ivl
    
    unit(7*24*60*60, "wk")
    unit(24*60*60, "d")
    unit(60*60, "h")
    unit(60, "m")
    times.append(f"{tsec}s")
    
    return "".join(times[:2])


@cache.cached(timeout=5, key_prefix="pods_dict")
def pods_dict():
    ret = kube.list_namespaced_pod('default', watch=False)

    svcs = {}

    for i in ret.items:
        restarts = 0
        containers = len(i.status.container_statuses)
        ready = 0
        started = 0
        restart_age = None
        restart_cause = None
        for c in i.status.container_statuses:
            if c.ready:
                ready += 1
            if c.started:
                started += 1
            restarts += c.restart_count
            if c.last_state.terminated:
                restart_age = mk_dt(datetime.now(timezone.utc)-c.last_state.terminated.finished_at)
                restart_cause = c.last_state.terminated.reason
    
        try:
            svc,deployment,pid = i.metadata.name.rsplit("-", 2)
        except:
            svc,deployment,pid = i.metadata.name,"",""

        if svc not in svcs:
            svcs[svc] = {}
        if deployment not in svcs[svc]:
            svcs[svc][deployment] = {}
        svcs[svc][deployment][pid] = {
            "age": mk_dt(datetime.now(timezone.utc)-i.status.start_time),
            "phase": i.status.phase,
            "ready": ready,
            "containers": containers,
            "restarts": restarts,
            "restart_age": restart_age,
            "restart_cause": restart_cause
        }
    
    return svcs


@api.route('/pods')
def pods_json():    
    return jsonify(pods_dict())


@api.route('/pods/text')
def pods():
    svcs = pods_dict()
    lines = []
    
    for svc,deployments in svcs.items():
        lines.append(svc)
        for deployment,pods in deployments.items():
            lines.append(f"  {deployment}")
            for pod,detail in pods.items():
                lines.append(f"    {pod}: {detail['phase']}, {detail['ready']}/{detail['containers']} ready, age {detail['age']}")
                if detail['restarts']:
                    lines.append(f"      {detail['restarts']} restarts; most recent was {detail['restart_cause']}, {detail['restart_age']} ago")
    
    return "\n".join(lines)


def init_app(app, url_prefix='/api/v1'):
    global parent_app
    parent_app = app
    app.register_blueprint(api, url_prefix=url_prefix)
    cache.init_app(app)
