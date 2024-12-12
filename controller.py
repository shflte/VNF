from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.app.wsgi import WSGIApplication, ControllerBase, route, Response
import json

rest_api_path = "/flow"


class FlowController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    _CONTEXTS = {"wsgi": WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(FlowController, self).__init__(*args, **kwargs)
        self.switches = {}
        self.wsgi = kwargs["wsgi"]
        self.wsgi.register(RestAPIController, {"app": self})

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        # Handler to set initial flow rules
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Save connected switch
        self.switches[datapath.id] = datapath

        # Add default flow rule to send unmatched packets to the controller
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match, instructions=inst
        )
        datapath.send_msg(mod)

    def install_flow(self, datapath_id, match, actions):
        datapath = self.switches.get(datapath_id)
        self.add_flow(datapath, 1, match, actions)
        self.logger.info(
            "Installed flow on switch {}: match={} actions={}".format(
                datapath_id, match, actions
            )
        )


class RestAPIController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(RestAPIController, self).__init__(req, link, data, **config)
        self.app = data["app"]

    @route("flow", rest_api_path, methods=["POST"])
    def set_flow(self, req, **kwargs):
        try:
            # Parse incoming JSON request
            data = json.loads(req.body)

            datapath_id = data["switch"]
            match_fields = data["match"]
            actions = data["actions"]

            # Build match and actions for ryu
            parser = self.app.switches[datapath_id].ofproto_parser
            match = parser.OFPMatch(**match_fields)
            action_list = [parser.OFPActionOutput(a["port"]) for a in actions]

            # Install the flow rule
            self.app.install_flow(datapath_id, match, action_list)

            return Response(
                content_type="application/json",
                body=json.dumps({"status": "success"}),
                status=200,
            )
        except Exception as e:
            return Response(
                content_type="application/json",
                body=json.dumps({"status": "error", "message": str(e)}),
                status=400,
            )
