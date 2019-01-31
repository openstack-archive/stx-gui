/* Namespace for core functionality related to Host Topology. */

horizon.host_topology = {
  model: null,
  svg:'#topology_canvas',
  svg_container:'#topologyCanvasContainer',
  detail_container:'#detail_view',
  zoom_container:'#zoom_container',
  alarm_tmpl: '#topology_template > .list_alarm',
  network_tmpl: '#topology_template > .network_container_normal',
  host_tmpl: '#topology_template > .host_body',
  segment_alarm_id: "300.005",
  locked_str: 'locked',
  zoom : null,
  network_index: {},
  reload_duration: 10000,
  labels: true,
  detail_url: null,
  selected_entity: null,
  network_height : 0,
  element_properties:{
    network_width:250,
    network_min_height:500,
    network_padding_top:20,
    top_margin:80,
    default_height:80,
    margin:48,
    host_x:98.5,
    port_text_margin:{x:8,y:-4},
    lldp_text_margin:{x:3,y:12},
    host_width:70,
    conn_margin:16, //28
    conn_height:6,
    conn_width:82,
    lldp_text_height:12,
    texts_bg_y:62,
    type_y:80,
    hostname_offset:17,
    cidr_margin:5,
    lldp_name_max_size_small:13,
    lldp_name_max_size:40,
    host_name_max_size:20,
    name_suffix:'..'
  },
  init:function() {
    var self = this;
    self.$container = $(self.svg_container);
    self.$loading_template = horizon.networktopologyloader.setup_loader($(self.$container));
    if($('#hosttopology').length === 0) {
      return;
    }
    self.color = d3.scale.category10();

    // Drag behaviour
    var svg = d3.select(self.svg);
    self.zoom = d3.behavior.zoom().on("zoom", self.zoomed);
    svg.call(self.zoom);

    // Unbind 'zoom' behaviour
    svg.on("dblclick.zoom", null);
    svg.on("wheel.zoom", null);
    svg.on("mousewheel.zoom", null);

    // Initialize label toggle button
    var labels = horizon.cookies.get('host_topo_labels');
    if (labels && (labels === "visible" || labels === "hidden")) {
      self.labels = labels;
    } else {
      self.labels = "visible";
      horizon.cookies.put('host_topo_labels',self.labels);
    }
    $('#toggleLabels > .btn').each(function(){
      var $this = $(this);
      if(self.labels === "hidden") {
        $this.addClass('active');
      } else {
        $this.removeClass('active');
      }
    });
    if (self.labels === "hidden") {
      $('#toggleLabels > .btn').trigger("click");
    }

    $('#toggleLabels > .btn').click(function(){
      if ($('#toggleLabels > .btn input').is(':checked')) {
        self.labels = "hidden"
      } else {
        self.labels = "visible"
      }
      $('.port_text, .lldp_text').attr("visibility", self.labels);
      horizon.cookies.put('host_topo_labels',self.labels);

      $('#toggleLabels > .btn').each(function(){
        var $this = $(this);
        if(self.labels === "hidden") {
          $this.addClass('active');
        } else {
          $this.removeClass('active');
        }
      });
    });

    // Initialize host list sorting behaviour
    $('#host_list_search').keyup(function(){
        var text = $(this).val().toLowerCase();
        $('#host_list > a').each(function(){
            var entry_text = $(this).text(),
                show_entry = entry_text.toLowerCase().indexOf(text) !== -1;
            $(this).toggle(show_entry);
        });
    });
    // Initialize datanet list sorting behaviour
    $('#network_list_search').keyup(function(){
        var text = $(this).val().toLowerCase();
        $('#network_list > a').each(function(){
            var entry_text = $(this).text(),
                show_entry = entry_text.toLowerCase().indexOf(text) !== -1;
            $(this).toggle(show_entry);
        });
    });

    this.$detail_view = $('#detail_view');
    this.$network_list = $('#network_list');
    this.$host_list = $('#host_list');

    self.load_host_info();
  },
  load_host_info:function(){
    var self = this;
    if($('#hosttopology').length === 0) {
      return;
    }
    $.getJSON($('#hosttopology').data('hosttopology') + '?' + $.now(),
      function(data) {
        self.model = data;
        self.data_convert();
        setTimeout(function(){
          self.load_host_info();
        }, self.reload_duration);
      }
    );
  },
  data_convert:function() {
    var self = this;
    var model = self.model;
    $.each(model.networks, function(index, network) {
      self.network_index[network.id] = index;
    });
    var element_properties = self.element_properties;
    self.network_height = element_properties.top_margin;

    // Skip straight to drawing if there are no networks
    if (model.networks.length <= 0) {
        self.draw_topology();
        self.$loading_template.hide();
        return;
    }

    // Remove hosts without worker functionality
    model.hosts = $.grep(model.hosts, function (host, i){
      if (host.subfunctions && host.subfunctions.indexOf('worker') !== -1){
        return true;
      }
      return false;
    })

    $.each(model.hosts, function(index, host) {
      var hasifs = (host.interfaces.length <= 0) ? false : true;

      // Attach alarms to this host
      host.alarm_level = 0; //0=No alarm, 4=critical
      host.alarms = [];
      $.each(model.alarms, function(index, alarm) {
        ids = alarm.entity_instance_id.split(".");
        for (i=0; i<ids.length; i++) {
          obj = ids[i].split('=')[1];
          if (obj == host.uuid || obj == host.hostname) {
            host.alarms.push(alarm);
            self.set_alarm_level(alarm, host);
            break;
          }
        }
      });

      host.connections = [];
      // 'expand' a single IF connected to many dnets into multiple 'connections'
      $.each(host.interfaces, function(index, interface) {
        var if_connections = []
        if (interface.datanetworks) {
          $.each(interface.datanetworks, function(index, datanet_name) {
            var connection = {}
            // Attach the interface to the connection
            connection.interface = interface;

            // Loop through networks and attach the full dnet to the connection
            $.each(model.networks, function(index, datanet){
              if (datanet_name == datanet.name) {
                connection.datanet = datanet;
              }
            });

            connection.id = interface.ifname + "-" + datanet_name;

            // search for and attach lldp info for the port
            connection.lldp_labels = [];
            $.each(host.lldpneighbours, function(index, n) {
              $.each(host.ports, function(index, port) {
                // match the neighbour to the port and the port to the IF
                if (port.interface_uuid == interface.uuid &&
                    n.port_uuid == port.uuid){
                  connection.lldp_labels.push(n.system_name + "/" + n.port_identifier);
                }
              });
            });

            // Check the host's alarms for the status of this connection
            connection.alarm_level = 0; //0=No alarm, 4=critical
            $.each(host.alarms, function(index, alarm) {
              ids = alarm.entity_instance_id.split(".");
              for (i=0; i<ids.length; i++) {
                obj = ids[i].split('=')[1];
                if (obj == interface.ifname || obj == interface.uuid) {
                  self.set_alarm_level(alarm, connection);
                  break;
                }
              }
            });
            if_connections.push(connection);
          });
        }
        host.connections = host.connections.concat(if_connections);
      });

      var hasconns = (host.connections.length <= 0) ? false : true;
      main_connection = self.select_main_connection(host.connections);
      host.parent_network = (hasconns) ? main_connection.datanet.id : self.model.networks[0].id;
      var height = element_properties.conn_margin*(host.connections.length - 1);
      host.lldp_heights = [];
      $.each(host.connections,function(index, connection) {
        if (connection.id !== main_connection.id){
          height += element_properties.lldp_text_height*(connection.lldp_labels.length);
          host.lldp_heights.push(element_properties.lldp_text_height*connection.lldp_labels.length);
        }
      });
      host.height = (height > element_properties.default_height) ? height :
                     element_properties.default_height;
      host.pos_y = self.network_height;
      host.port_height = element_properties.conn_height;
      host.port_margin = element_properties.conn_margin;
      self.network_height += host.height + element_properties.margin;

      // Add host to its table
      found = false;
      self.$host_list.find('a').each(function(index) {
        if ($(this).text().trim() == host.hostname){
          found = true;
          return false;
        }
      });
      if (!found) {
        self.$host_list.append(
          $('<a>')
            .attr('href',"#")
            .attr('class',"list-group-item list-group-item-action")
            .attr("id","host-" + host.hostname)
            .append(host.hostname)
            .on('click',function(d){
              self.zoom_to(d,host);
              self.select_host(host);
            })
          );
        // Append the alarm icon to the host entry
        self.$host_list.find('a#host-'+host.hostname).prepend(d3.select(self.alarm_tmpl).node().cloneNode(true));
      }
      // Set the list's alarm level for this host
      list_alarm = d3.select('#host_list a#host-'+host.hostname+' .alarm');
      list_alarm.classed("level_1 level_2 level_3 level_4", false);
      list_alarm.classed('level_'+host.alarm_level, true);

    });

    $.each(model.networks, function(index, network) {
      network.hosts = [];
      network.connected_hosts = [];

      // Attach alarms to the network
      network.alarms = [];
      network.alarm_level = 0;
      $.each(model.alarms, function(index, alarm) {
        ids = alarm.entity_instance_id.split(".");
        for (i=0; i<ids.length; i++) {
          obj = ids[i].split('=')[1];
          if (obj == network.id || obj == network.name) {
            network.alarms.push(alarm);
            self.set_alarm_level(alarm, network);
            break;
          }
        }
      });

      $.each(model.hosts,function(index, host) {
        if(network.id === host.parent_network) {
          network.hosts.push(host);
        }

        // Add any hosts with a connection to this dnet (for use in list linking)
        // And propagate the dnet's alarm status to the connection
        $.each(host.connections,function(index, connection) {
          if (connection.datanet.name === network.name){
            network.connected_hosts.push(host);
            if (network.alarm_level > connection.alarm_level)
              connection.alarm_level = network.alarm_level;
            return false;
          }
        });
      });

      // Add network to its table
      found = false;
      self.$network_list.find('a').each(function(index) {
        if ($(this).text().trim() == network.name){
          found = true;
          return false;
        }
      });
      if (!found) {
        self.$network_list.append(
          $('<a>')
            .attr('href',"#")
            .attr('class',"list-group-item list-group-item-action")
            .attr("id","net-" + network.name)
            .append(network.name)
            .on('click',function(d){
              self.zoom_to(d,network);
              self.select_network(network);
            })
          );
        // Append the alarm icon to the network entry
        self.$network_list.find('a#net-'+network.name).prepend(d3.select(self.alarm_tmpl).node().cloneNode(true));
      }
      // Set the list's alarm level for this host
      list_alarm = d3.select('#network_list a#net-'+network.name+' .alarm');
      list_alarm.classed("level_1 level_2 level_3 level_4", false);
      list_alarm.classed('level_'+network.alarm_level, true);

    });
    self.network_height += element_properties.top_margin;
    self.network_height = (self.network_height > element_properties.network_min_height) ?
      self.network_height : element_properties.network_min_height;

    // console.log(model); // Uncomment for console debug logs
    self.draw_topology(); 
    self.$loading_template.hide();
  },
  load_detail:function(spin){
    scroll = typeof b !== 'undefined' ? b : false;
    var self = this;

    // Load host into detail view
    if (self.detail_url === null)
      return;
    if (spin) {
      $(self.detail_container).html("");
      self.$loading_detail_template = horizon.networktopologyloader.setup_loader($(self.detail_container));
    }
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() {
      if (this.readyState == this.DONE) {
        if(this.status == 200) {
          if (this.responseText.indexOf('main_content') !== -1 ||
              this.responseText.indexOf('login-title') !== -1) {
            // We've been redirected to a fallback url (full page or login)
            self.$loading_detail_template.hide();
            $(self.detail_container).html("Error retrieving details from url " + self.detail_url + " Status: " + this.status);
          } else {
            self.detail_callback(self, this.responseText);
            self.$loading_detail_template.hide();
          }
          return;
        };
        self.$loading_detail_template.hide();
        $(self.detail_container).html("Error retrieving details from url " + self.detail_url + " Status: " + this.status);
      }
    }
    tab = $('#detail_view .nav-tabs li.active a').attr('href');
    xmlHttp.open("GET", (tab != undefined) ? self.detail_url+tab : self.detail_url, true);
    xmlHttp.send(null);
  },
  detail_callback:function(self, response) {
    tab_index = this.$detail_view.find('.nav-tabs li.active').index();
    $(self.detail_container).html(response);
    if (tab_index !== -1) {
      this.$detail_view.find('.nav-tabs li:nth-child('+(tab_index+1)+') a').trigger('click');
    }

    // Special functionality on loaded host detail view
    this.$detail_view.find('table#interfaces tr:not(:first):not(:last)').each(function(i,d) {
      $.each(self.selected_entity.alarms, function(index, alarm) {
        $(d).removeClass('status_down')
        if (self.str_in_alarm($(d).attr('data-display'), alarm) ||
            self.str_in_alarm($(d).attr('data-object-id'), alarm)) {
          $(d).addClass('status_down')
        }
      });
    });
    // Special functionality on loaded datanet detail view
    this.$detail_view.find('table#provider_network_ranges tr:not(:first):not(:last)').each(function(i,d) {
      $.each(self.selected_entity.alarms, function(index, alarm) {
        $(d).removeClass('status_down')
        if (self.segment_in_alarm(parseInt($(d).children("td:nth-child(4)").text()), parseInt($(d).children("td:nth-child(5)").text()), alarm)) {
          $(d).addClass('status_down')
        }
      });
    });

  },
  segment_in_alarm:function(min, max, alarm) {
    var self = this;
    if (alarm.alarm_id !== self.segment_alarm_id)
      return false; // Unrelated alarm
    if (alarm.reason_text.indexOf("ranges") == -1)
      return false; // Generic datanetwork alarm, for flat networks

    // Retrieve the csv (with spaces) of failed segment ranges
    desc = alarm.reason_text.substring(alarm.reason_text.indexOf("ranges")+7, alarm.reason_text.indexOf(" on host"));
    desc = desc.split(", ");

    for (i=0; i<desc.length; i++) {
      if (desc[i].indexOf("-") !== -1) {
        // A range has failed
        alarm_min = desc[i].split("-")[0];
        alarm_max = desc[i].split("-")[1];
        if (min == alarm_min && max == alarm_max)
          return true;
      } else {
        // A single segment has failed
        if (desc[i] == min && desc[i] == max)
          return true;
      }
    }
    return false;
  },
  str_in_alarm:function(entity_str, alarm) {
    ids = alarm.entity_instance_id.split(".");
    for (i=0; i<ids.length; i++) {
      obj = ids[i].split('=')[1];
      if (obj == entity_str) {
        return true
      }
    }
    return false;
  },
  select_host:function(host, scroll) { // pick a host from it's list
    scroll = typeof b !== 'undefined' ? b : false;
    var self = this;

    $('#lists_container a').removeClass('active related');
    $('#network_list').scrollTop(0);
    entry = $('#host_list a#host-'+host.hostname);
    if (scroll) {
      entry[0].scrollIntoView();
    }
    entry.addClass('active');
    $.each(host.connections, function(index, connection) {
      connected_entry = $('#network_list a#net-'+connection.datanet.name);
      connected_entry.addClass('related');
      connected_entry.prependTo('#network_list');
    });

    self.detail_url = $(location).attr('href')+host.id+"/host/";
    $.each(self.model.hosts, function(index, model_host) {
      if (model_host.hostname === host.hostname)
        self.selected_entity = model_host;
    });

    self.load_detail(true);

    horizon.cookies.put('host_topo_selected', "#host_list a#host-"+host.hostname);
  },
  select_network:function(network, scroll) { // pick a network from it's list
    scroll = typeof b !== 'undefined' ? b : false;
    var self = this;

    $('#lists_container a').removeClass('active related');
    $('#host_list').scrollTop(0);
    entry = $('#network_list a#net-'+network.name)
    if (scroll) {
      entry[0].scrollIntoView();
    }
    entry.addClass('active');
    $.each(network.connected_hosts, function(index, host) {
      connected_entry = $('#host_list a#host-'+host.hostname);
      connected_entry.addClass('related');
      connected_entry.prependTo('#host_list');
    });

    self.detail_url = $(location).attr('href')+network.id+"/datanet/"
    $.each(self.model.networks, function(index, model_network) {
      if (model_network.name === network.name)
        self.selected_entity = model_network;
    });
    self.load_detail(true);

    horizon.cookies.put('host_topo_selected', "#network_list a#net-"+network.name);
  },
  zoom_to:function(d, entity) {
    var self = this;

    if (entity.hostname){
      obj = d3.select('#topology_canvas #id_host_'+entity.hostname);
    } else {
      obj = d3.select('#topology_canvas #id_net_'+entity.name);
    }
    current = d3.transform($('#zoom_container').attr("transform")).translate; //Current zoom location
    target = d3.transform(obj.attr("transform")).translate; //transform of the selected element

    self.add_glow(entity);

    //New coordinates centered to the view
    new_x = -target[0] + $(self.svg).width()/2;
    if (entity.hostname) {
      net_x = d3.transform($("#id_host_"+entity.hostname).parent().attr("transform")).translate[0];
      new_x -= net_x;
    }
    new_y = (entity.hostname) ? -target[1] + $(self.svg).height()/2 : current[1];  // Ignore y change if zooming to pnet

    // If scrolling past end on the left or right, stop at edge
    if (new_x > 50)
      new_x = 50;
    else if (new_x < (-parseInt($(self.zoom_container)[0].getBoundingClientRect().width) + $(self.svg).width()))
      new_x = -parseInt($(self.zoom_container)[0].getBoundingClientRect().width) + $(self.svg).width() - 100;

    translate = [new_x , new_y];

    // Only zoom if entity is not already visible
    if (entity.hostname) {
      // Note: visible_ is the direct offset from the viewport to the entity
      visible_x = net_x + target[0] + current[0];
      visible_y = target[1] + current[1];
      if (!(visible_x < 0 ||
            visible_x > $(self.svg).width() - self.element_properties.host_width ||
            visible_y < 0 ||
            visible_y > $(self.svg).height() - self.element_properties.host_width))
        return;
    } else {
      if (!(target[0] < -current[0] ||
            target[0] > -current[0] + $(self.svg).width() - 17))
        return;
    }

    d3.select(self.zoom_container).transition().duration(700)
        .attr('transform', "translate(" + translate[0] + "," + translate[1] + ")scale(1)");

    // Update the zoom to the new location
    self.zoom.scale(1);
    self.zoom.translate(translate);

    // Fix pnet names to top of view
    if (new_y > 25){
      new_y = 25;
    }

    d3.selectAll('svg#topology_canvas .network-name').transition().duration(700)
          .attr('y',-new_y + 20);

    horizon.cookies.put('host_topo_position', translate);
  },
  zoomed:function(given_translate) {
    if (typeof given_translate !== 'undefined')
      translate = given_translate;
    else
      translate = d3.event.translate;

    this.$svg_canvas = $('svg#topology_canvas');
    var zoom_container = d3.select('#zoom_container');
    zoom_container.attr("transform", "translate(" + translate + ")");

    // Fix pnet names to top of view
    if (-translate[1] > parseInt(this.$svg_canvas.find('.network-rect')[0].getAttribute("height"))) {
      // Lock to bottom of network bars
      this.$svg_canvas.find('.network-name').attr('y', parseInt(this.$svg_canvas.find('.network-rect')[0].getAttribute("height")) + 22);
    } else if (translate[1] < 25){
      // Scrolling with bars
      this.$svg_canvas.find('.network-name').attr('y',-translate[1] + 20);
    } else {
      // Lock to top of network bars
      this.$svg_canvas.find('.network-name').attr('y', -5);
    }

    horizon.cookies.put('host_topo_position', translate);
  },
  add_glow:function(entity) {
    if (entity.hostname){
      highlight = d3.select('#topology_canvas #id_host_'+entity.hostname+' .frame');
    } else {
      highlight = d3.select('#topology_canvas #id_net_'+entity.name+' .network-rect');
    }
    // Deselect everything and add glow to newly selected element
    d3.selectAll('.host .frame, .network .network-rect').classed('selected', false);
    highlight.classed('selected', true);
  },
  draw_topology:function() {
    var self = this;
    $(self.svg_container).removeClass('noinfo');
    if (self.model.networks.length <= 0) {
      $('g.network').remove();
      $(self.svg_container).addClass('noinfo');
      return;
    }

    var zoom_container = d3.select(self.zoom_container);
    var svg = d3.select(self.svg);
    var element_properties = self.element_properties;
    var network = zoom_container.selectAll('g.network')
      .data(self.model.networks);

    var network_enter = network.enter()
      .append('g')
      .attr('class','network')
      .each(function(d,i){
        this.appendChild(d3.select(self.network_tmpl).node().cloneNode(true));
        var $this = d3.select(this).select('.network-rect');
        $this
          .on('mouseover',function(){
            $this.transition().style('fill', function() {
              return d3.rgb(self.get_network_color(d.id)).brighter(0.5);
            });
          })
          .on('mouseout',function(){
            $this.transition().style('fill', function() {
              return self.get_network_color(d.id);
            });
          })
          .on('click',function(){
            // Select the pnet from the list
            self.add_glow(d);
            self.select_network(d,true);
          });
      });

    network
      .attr('id',function(d) { return 'id_net_' + d.name; })
      .attr('transform',function(d,i){
        return 'translate(' + element_properties.network_width * i + ',' + 0 + ')';
      })
      .select('.network-rect')
      .attr('height', function(d) { return self.network_height; })
      .style('fill', function(d) { return self.get_network_color(d.id); });
    network
      .select('.network-rect-hash')
      .attr('height', function(d) { return self.network_height; })
    network
      .select('.network-name')
      .text(function(d) { return d.name; });

    // Set the alarm styles for the datanet
    network.each(function(d) {
      if (d.alarm_level) {
        d3.select(this).select('.network-rect-hash').attr('visibility','visible');
      } else {
        d3.select(this).select('.network-rect-hash').attr('visibility','hidden');
      }

      d3.select(this).select('.alarm').classed('level_1 level_2 level_3 level_4',false);
      d3.select(this).select('.alarm').classed('level_'+d.alarm_level,true);
    });

    $('[data-toggle="tooltip"]').tooltip({container: 'body'});

    network.exit().remove();

    var host = network.selectAll('g.host')
      .data(function(d) { return d.hosts; });

    var host_enter = host.enter()
      .append("g")
      .attr('class','host')
      .each(function(d,i){
        var host_template = self['host_tmpl'];
        this.appendChild(d3.select(host_template).node().cloneNode(true));
        var $this = d3.select(this);
        $this
          .on('mouseover',function(){
            $this.selectAll('.frame, .texts_bg, .status>circle, .alarm>circle').transition().style('stroke', function() {
              return d3.rgb("#222").brighter(1.8);
            });
            $this.selectAll('.texts_bg, .status>rect').transition().style('fill', function() {
              return d3.rgb("#222").brighter(1.8);
            });
          })
          .on('mouseout',function(){
            $this.selectAll('.frame, .texts_bg, .status>circle, .alarm>circle').transition().style('stroke', function() {
              return d3.rgb("#222");
            });
            $this.selectAll('.texts_bg, .status>rect').transition().style('fill', function() {
              return d3.rgb("#222");
            });
          });
      });

    host_enter
      .on('click',function(d){
        // Select the host from the list
        self.add_glow(d);
        self.select_host(d,true);
      });

    host
      .attr('id',function(d) { return 'id_host_' + d.hostname})
      .attr('transform',function(d,i){
        return 'translate(' + element_properties.host_x + ',' + d.pos_y  + ')';
      })
      .select('.frame')
      .attr('height',function(d) { return d.height; });
    host
      .select('.texts_bg')
      .attr('y',function(d) {
        return element_properties.texts_bg_y + d.height - element_properties.default_height;
      });
    host
      .select('.name')
      .text(function(d) { return d.hostname ? self.string_truncate(d.hostname, element_properties.host_name_max_size) : "Unconfigured";
      })
      .attr('y',function(d) {
        return element_properties.type_y + d.height - element_properties.default_height + element_properties.hostname_offset;
      });
    host
      .select('.status')
      .attr('transform',function(d) {
        return 'translate(' + 0 + ',' + d.height/2  + ')';
      });

    // Logic for looks of host (status, alarms)
    host.each(function(d) {
      if (d.administrative == self.locked_str) {
        d3.select(this).select('.status').classed('unlocked',false);
      } else {
        d3.select(this).select('.status').classed('unlocked',true);
      }
      d3.select(this).select('.alarm').classed('level_1 level_2 level_3 level_4',false);
      d3.select(this).select('.alarm').classed('level_'+d.alarm_level,true);
    });

    host.exit().remove();

    var port = host.select('g.connections')
      .selectAll('g.port')
      .data(function(d) {return d.connections; });

    var port_enter = port.enter()
      .append('g')
      .attr('class','port')
      .attr('id',function(d) { return 'id_' + d.id; });

    port_enter
      .append('line')
      .attr('class','port_line');

    port_enter
      .append('text')
      .attr('class','port_text');

    host.select('g.connections').each(function(d,i){
      this._portdata = {};
      this._portdata.ports_length = d.ports.length;
      this._portdata.parent_network = d.parent_network;
      this._portdata.host_height = d.height;
      this._portdata.port_height = d.port_height;
      this._portdata.port_margin = d.port_margin;
      this._portdata.lldp_heights = d.lldp_heights;
      this._portdata.left = 0;
      this._portdata.right = 0;
    });

    port.each(function(d,i){
      var index_diff = self.get_network_index(this.parentNode._portdata.parent_network) -
        self.get_network_index(d.datanet.id);
      this._index_diff = index_diff = (index_diff >= 0)? ++index_diff : index_diff;
      this._direction = (this._index_diff < 0)? 'right' : 'left';
      this._index  = this.parentNode._portdata[this._direction] ++;
      this._lldp_label_count = d.lldp_labels.length;
    });

    port.attr('transform',function(d,index){
      var x = (this._direction === 'left') ? 0 : element_properties.host_width;
      var ports_length = this.parentNode._portdata[this._direction];
      var distance = this.parentNode._portdata.port_margin; // Height of IF name + port height
      if (this._direction == 'right'){
        var y = this.parentNode._portdata.port_margin;
        for (i=0; i < this._index; i++){
          y += distance + this.parentNode._portdata.lldp_heights[i]; //sum previous lldp label spacings
        }
      } else {
        var y = (this.parentNode._portdata.host_height -
          (ports_length -1)*distance)/2 + this._index*distance;
      }
      return 'translate(' + x + ',' + y + ')';
    });

    port
      .select('.port_line')
      .attr('stroke-width',function(d,i) {
        return this.parentNode.parentNode._portdata.port_height;
      })
      .attr('stroke', function(d, i) {
        return self.get_network_color(d.datanet.id);
      })
      .attr('x1',0).attr('y1',0).attr('y2',0)
      .attr('x2',function(d,i) {
        var parent = this.parentNode;
        var width = (Math.abs(parent._index_diff) - 1)*element_properties.network_width +
          element_properties.conn_width;
        return (parent._direction === 'left') ? -1*width : width;
      });

    // Set connection text
    port
      .select('.port_text')
      .attr('x',function(d) {
        var parent = this.parentNode;
        if (parent._direction === 'left') {
          d3.select(this).classed('left',true);
          return element_properties.port_text_margin.x*-1;
        } else {
          d3.select(this).classed('left',false);
          return element_properties.port_text_margin.x;
        }
      })
      .attr('y',function(d) {
        return element_properties.port_text_margin.y;
      })
      .text(function(d) {
        return d.interface.ifname;
      });

    // Set the alarmed looks for the connection
    port.each(function(d) {
      if (d.alarm_level) {
        d3.select(this).select('.port_line').classed('port_alarmed',true);
      } else {
        d3.select(this).select('.port_line').classed('port_alarmed',false);
      }
    });

    port
      .each(function(d) {
        var parent = this.parentNode;
        var node = d3.select(this);
        if (Math.abs(node.select('.port_line').attr('x2')) <= self.element_properties.conn_width)
          cutoff = self.element_properties.lldp_name_max_size_small;
        else
          cutoff = self.element_properties.lldp_name_max_size;

        node.selectAll(".lldp_text").remove();
        $.each(d.lldp_labels, function(index, label) {
          node.append("text")
            .text(self.string_truncate(label, cutoff))
            .attr('data-toggle',function(d) { return label.length > cutoff ? 'tooltip' : null})
            .attr('data-placement',function(d) { return label.length > cutoff ? 'bottom' : null})
            .attr('title',function(d) { return label.length > cutoff ? label : null})
            .attr('class','lldp_text')
            .attr('x',function(d) {
              if (this.parentNode._direction === 'left') {
                d3.select(this).classed('left',true);
                d3.select(this).classed('right',false);
                return parseInt(node.select('.port_line').attr('x2'))+element_properties.lldp_text_margin.x;
              }
               else {
                d3.select(this).classed('left',false);
                d3.select(this).classed('right',true);
                return parseInt(node.select('.port_line').attr('x2'))-element_properties.lldp_text_margin.x;
              }
            })
            .attr('y',function(d) {
              return element_properties.lldp_text_margin.y + element_properties.lldp_text_height*index;
            })
        });
      })

    $('.tooltip').remove();
    $('[data-toggle="tooltip"]').tooltip({container: 'body'});

    port.exit().remove();

    // Ensure label visibility is set
    $('.port_text, .lldp_text').attr("visibility", self.labels);

    // Load any saved entity or zoom position or update the zoom to the starting location
    var translate = horizon.cookies.get('host_topo_position');
    var selected = horizon.cookies.get('host_topo_selected');
    if (selected && self.selected_entity == null) {
      $(selected).click();
    }
    else if (translate) {
      self.zoom.translate(translate);
      self.zoomed(translate);
    }
    else if (!selected && !translate) {
      self.zoom.translate([50,25]);
    }

    // Update selected host with fresh data + refresh detail view
    if (self.selected_entity && self.selected_entity.hostname){
      $.each(self.model.hosts, function(index, model_host) {
        if (model_host.hostname === self.selected_entity.hostname)
          self.selected_entity = model_host;
      });
    } else if (self.selected_entity){
      $.each(self.model.networks, function(index, model_network) {
        if (model_network.name === self.selected_entity.name)
          self.selected_entity = model_network;
      });
    }
    self.load_detail(false);
  },
  get_network_color: function(network_id) {
    return this.color(this.get_network_index(network_id));
  },
  get_network_index: function(network_id) {
    return this.network_index[network_id];
  },
  select_main_connection: function(connections){
    var _self = this;
    var main_conn_index = 0;
    var MAX_INT = 4294967295;
    var min_conn_length = MAX_INT;
    $.each(connections, function(index, connection){
      var conn_length = _self.sum_conn_length(connection.datanet, connections);
      if(conn_length < min_conn_length){
        min_conn_length = conn_length;
        main_conn_index = index;
      }
    });
    return connections[main_conn_index];
  },
  sum_conn_length: function(datanet, connections){
    var self = this;
    var sum_conn_length = 0;
    var base_index = self.get_network_index(datanet.id);
    $.each(connections, function(index, connection){
      sum_conn_length += base_index - self.get_network_index(connection.datanet.id);
    });
    return sum_conn_length;
  },
  set_alarm_level: function(alarm, entity) {
    if (alarm.severity == "critical") {entity.alarm_level = 4;}
    if (alarm.severity == "major" && entity.alarm_level < 4) {entity.alarm_level = 3;}
    if (alarm.severity == "minor" && entity.alarm_level < 3) {entity.alarm_level = 2;}
    if (alarm.severity == "warning" && entity.alarm_level < 2) {entity.alarm_level = 1;}
  },
  string_truncate: function(string, max_size) {
    var self = this;
    var str = string;
    var suffix = self.element_properties.name_suffix;
    var bytes = 0;
    for (var i = 0;  i < str.length; i++) {
      bytes += str.charCodeAt(i) <= 255 ? 1 : 2;
      if (bytes > max_size) {
        str = str.substr(0, i) + suffix;
        break;
      }
    }
    return str;
  }
};
