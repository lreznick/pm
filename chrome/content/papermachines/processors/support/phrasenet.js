var pattern = data["PATTERN"];
var numnodes = 50;
d3.select("body").append("h1").text(pattern);
var fontSize = d3.scale.log().range([10,32]);
var linkSize = d3.scale.linear().range([2,10]);

var parseDate = d3.time.format("%Y-%m-%d").parse;
var timedata = data["DATA"]['times'].sort(function(a, b){
    return parseDate(a.t)-parseDate(b.t); 
});
var edgedata = data["DATA"]['edges'];

var margin = {top: 10, right: 10, bottom: 100, left: 40},
    width = 960 - margin.left - margin.right,
    pheight = 800,
    margin2 = {top: 10+pheight, right: 10, bottom: 20, left: 40},
    cheight = 500;

var svg = d3.select("body").append("svg")
  .attr("width", width + margin.left + margin.right)
  .attr("height", pheight + cheight + margin.top + margin.bottom);


var nodes=[];
var edges=[];

var fontSize = d3.scale.log().range([10,32]);
var linkSize = d3.scale.linear().range([2,10]);

var diagonal = d3.svg.diagonal()
  .source(function (d) {
    var b_s = d3.select("#node" + d.source.name)[0][0].getBBox(),
        b_t = d3.select("#node" + d.target.name)[0][0].getBBox();

    return {'x': d.source.x, 'y': d.source.y + (d.source.y < d.target.y ? b_s.height * 0.5 : b_s.height * -0.5)};

  })
  .target(function (d) {
    var b_s = d3.select("#node" + d.source.name)[0][0].getBBox(),
        b_t = d3.select("#node" + d.target.name)[0][0].getBBox();

    return {'x': d.target.x, 'y': d.target.y + (d.source.y < d.target.y ? b_t.height * -0.5 : b_t.height * 0.5)};
  });

svg.append("svg:defs").selectAll("marker")
    .data(["defaultmarker"])
  .enter().append("svg:marker")
    .attr("id", String)
    .attr("viewBox", "0 0 10 10")
    .attr("refX", 0)
    .attr("refY", 5)
    .attr("markerWidth", 4)
    .attr("markerHeight", 3)
    .attr("markerUnits", "strokeWidth")
    .attr("orient", "auto")
  .append("svg:path")
    .attr("d", "M0,0L10,5L0,10z");

var force = d3.layout.force().size([width, pheight])
    .distance(100)
    .charge(-300)
    .gravity(0.15);

function collide(d) {
  var b = d3.select("#node" + d.name.toString())[0][0].getBBox(),
    nx1 = b.x,
    nx2 = b.x + b.width,
    ny1 = b.y,
    ny2 = b.y + b.height;

  return function (quad, x1, y1, x2, y2) {
    if (quad.point && (quad.point !== d)) {
      var b2 = d3.select("#node" + quad.point.name.toString())[0][0].getBBox(),
        ox1 = b2.x,
        ox2 = b2.x + b2.width,
        oy1 = b2.y,
        oy2 = b2.y + b2.height,
        x = nx1 - ox1,
        y = ny1 - oy1;

      if (nx1 <= ox2 && ox1 <= nx2) { // overlap in x's
        d.x += x * 0.005;
        quad.point.x -= x * 0.005;
      }

      if (ny1 <= oy2 && oy1 <= ny2) { // overlap in y's
        d.y += y * 0.005;
        quad.point.y -= y * 0.005;
      }
    }

    return x1 > nx2 || x2 < nx1 || y1 > ny2 || y2 < ny1;
  };
}


var x = d3.time.scale()
    .range([0, width])
    .domain(d3.extent(timedata, function(d) { return parseDate(d.t); }));

var y = d3.scale.linear()
    .range([cheight, 0])
    .domain([0, d3.max(timedata, function(d) { return d.c; })]);

var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom");

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");

var brush = d3.svg.brush()
    .x(x)
    .on("brushend", brushed);

var area = d3.svg.area()
    .x(function(d) {return x(parseDate(d.t));})
    .y0(function(d) {return y(0);})
    .y1(function(d) {return y(d.c); });

var context = svg.append("g")
  .attr("class", "context")
  .append("g")
  .attr("transform", "translate(" + margin2.left + "," + margin2.top + ")");

  context.append("path")
      .datum(timedata)
      .attr("class", "area")
      .attr("d", area);

  context.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + cheight + ")")
      .call(xAxis);

 context.append("g")
      .attr("class", "x brush")
      .call(brush)
    .selectAll("rect")
      .attr("y", -6)
      .attr("height", cheight + 7);

  context.append("g")
      .attr("class", "y axis")
      .call(yAxis)
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", ".71em")
      .style("text-anchor", "end")
      .text("Count");

function brushed() {
  var period = brush.extent();
  if (!brush.empty()) updatePhrases(dunning(period[0], period[1]), 0, function(d){return d[1];});
  return true;
}

function dunning(p1, p2){
  var i = 0;
  var dvals = [];
  for (i = 0; i<edgedata.length; i++){
    var d = edgedata[i];
    var edge = d.p;
    var times = d.t;
    if (Object.keys(times).length>1){
    var o = 0;
    var e = 0;
    for (var t in times){
      var count = times[t];
      var time = parseDate(t);
      if ((time<p2)&&(time>p1)) o+=count
      else e+=count;
    }
    if ((o>0)&&(e>0)) {
      dvals.push([edge, (o*(Math.log(o/e)))]);
    }
  }
  }
  return dvals;
}
//add datum to array, if necessary; return index of datum in array
function getorInsertNode(arr, datum, weight){
  var i;
  for (i = 0; i<arr.length; i++){
    if (arr[i].name == datum) {
      arr[i].weight += weight;
      return i;
    }
  }
  var i = arr.push({'name':datum, 'weight':weight});
  return i-1;
}

//given array of ["source,target", weight]
function getData(d, accessor, f){
  var i;
  d.sort(function(a, b){return f(b)-f(a);});
  var stop = Math.min(numnodes, d.length-1);
  for(i=0; i<stop; i++){
    var edge = d[i][accessor];
    var weight = f(d[i]);
    var s =  edge.split(","); var source = s[0]; var target = s[1];
    var si = getorInsertNode(nodes, source, weight);
    var ti = getorInsertNode(nodes, target, weight);
    edges.push({'source': si, 'target': ti, 'weight': weight, 'id': edge});
  }
}

function updatePhrases(d, a, f){
  nodes = [];
  edges = [];
  getData(d, a, f);
  console.log(nodes);
  var vals = nodes.map(function (d) { return d.weight});
  var e = d3.extent(vals); console.log(e);
  if (e[0] <= 0) e[0] = 1;
  fontSize = d3.scale.log().clamp(true).range([10,32]).domain(e);

  vals = edges.map(function (d) { return d.weight});
  linkSize = linkSize.copy().domain(d3.extent(vals));
  

  force.nodes(nodes)
      .links(edges)
      .start();

  var node = svg.selectAll(".node")
      .data(nodes, function(d){return d.name;});

  var nodeEnter = node.enter().append("svg:g")
      .attr("class", "node")
      .call(force.drag);

  nodeEnter.append("text")
      .attr("dx", 0)
      .attr("dy", ".35em")
      .style("font-size", function (d) { return fontSize(d.weight); })
      .attr("id", function (d, i) { return "node" + d.name;})
      .text(function(d) { return d.name; });

  node.exit().transition(1000).delay(500).style("color", "red").remove();

  var link = svg.selectAll(".link")
      .data(edges, function(d){d.id});

  var linkEnter = link.enter().append("path")
      .attr("class", "link")
      .style("stroke-width", function (d) { return linkSize(d.weight);})
      .style("stroke", "#000")
      .attr("d", diagonal)
      .attr("marker-end", "url(#defaultmarker)");

  link.exit().transition(3000).style("stroke", "red").remove();

force.on("tick", function() {
  link.attr("d", diagonal);

  node.attr("transform", function(d) {
    d.x = Math.max(fontSize(d.weight), Math.min(d.x, width - fontSize(d.weight)));
    d.y = Math.max(fontSize(d.weight), Math.min(d.y, pheight - fontSize(d.weight)));
  return "translate(" + d.x + "," + d.y + ")"; });
});

}

updatePhrases(edgedata, "p", function(d){
  var t = d.t;
  var sum = 0;
  for (var key in t){
    sum += t[key];
  }
  return sum;
});