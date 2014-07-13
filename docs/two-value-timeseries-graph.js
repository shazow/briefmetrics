'use strict';

Dashboard.TwoValueGraph = Dashboard.DiagnosticChart.extend({

  ascendingTime: function(t1, t2) {
    if (t1.time < t2.time) { return -1; }
    if (t1.time > t2.time) { return 1; }
    return 0;
  },

  transformData: function() {
    // sort by time ascending (oldest to newest)
    this.data.sort(this.ascendingTime);
  },

  valueExtent: function() {
    var self = this;
    return [0, d3.max(this.data.map(function(p) {
      return Math.max(p[self.get('a.key')], p[self.get('b.key')]);
    }))];
  }.property('data', 'a', 'b'),

  setup: function() {
    var self = this;
    this._super();

    this.valueScale = d3.scale.linear()
      .domain(self.get('valueExtent'))
      .nice(self.get('tickCount'));

    this.valueAxis = d3.svg.axis()
      .scale(this.valueScale)
      .tickPadding(5)
      .ticks(self.get('tickCount'))
      .tickFormat(this.transformLabelString)
      .orient('left');

    // draw axes and border underneath data
    this.valueAxisg = this.axes.append('g')
      .classed('axis', true);

    this.chartBorder = this.axes.append('rect')
      .classed('chartborder', true)
      .attr('x', this.dimensions.padding.left)
      .attr('y', this.dimensions.padding.top);

    // draw data
    // The reason this doesn't happen in render is that
    // the line/areas will automatically alter the the shape.
    ['a', 'b'].forEach(function(key) {
      var item = self.get(key);
      key = key.toUpperCase();

      self["area" + key] = d3.svg.area()
        .x(function(d) { return self.timeScale(d.time); })
        .y1(function(d) { return self.valueScale(d[item.key]); })
        .interpolate('step-after');

      self["line" + key] = d3.svg.line()
        .x(function(d) { return self.timeScale(d.time); })
        .y(function(d) { return self.valueScale(d[item.key]); })
        .interpolate('step-after');

      self["area" + key + "Path"] = self.container.append('path')
        .datum(self.data)
        .classed('area', true)
        .classed(item.class, true);

      self["line" + key + "Path"] = self.container.append('path')
        .datum(self.data)
        .classed('line', true)
        .classed(item.class, true);

      self["hover" + key + "TextKnockout"] = self.hoverText.append('text')
        .classed('knockout', true)
        .attr('text-anchor', 'end')
        .attr('x', 0)
        .attr('y', 50);

      self["hover" + key + "Text"] = self.hoverText.append('text')
        .classed(item.class, true)
        .attr('text-anchor', 'end')
        .attr('x', 0)
        .attr('y', 50);
    });

    return this;
  },

  resize: function() {
    this._super();
    this.valueScale.rangeRound([this.dimensions.innerHeight, 0]);
    this.valueAxis.tickSize(this.dimensions.innerWidth, 0);
    this.areaA.y0(this.dimensions.innerHeight);
    this.areaB.y0(this.dimensions.innerHeight);
    this.valueAxisg
      .attr("transform", "translate(%@, %@)".fmt(
        this.dimensions.width - this.dimensions.padding.right,
        this.dimensions.padding.top));
    this.chartBorder
      .attr('width', this.dimensions.innerWidth)
      .attr('height', this.dimensions.innerHeight);

    return this;
  },


  render: function() {
    this._super();
    this.valueAxisg.call(this.valueAxis);

    ['a', 'b'].forEach(function(key) {
      key = key.toUpperCase();
      this["area" + key + "Path"].attr('d', this["area" + key]);
      this["line" + key + "Path"].attr('d', this["line" + key]);
    }, this)

    return this;
  },

  renderHoverValues: function(values) {
    var yA = this.valueScale(values[this.get('a.key')]);
    var yB = this.valueScale(values[this.get('b.key')]);

    var top = {
      raw: values[this.get('a.key')],
      y: yA <= yB ? yA : yB,
      text: this.transformLabelString(yA <= yB ? values[this.get('a.key')] : values[this.get('b.key')]),
      knockout: yA <= yB ? this.hoverATextKnockout : this.hoverBTextKnockout,
      hover: yA <= yB ? this.hoverAText : this.hoverBText,
    };

    var bottom = {
      raw: values[this.get('b.key')],
      y: yA <= yB ? yB : yA,
      text: this.transformLabelString(yA <= yB ? values[this.get('b.key')] : values[this.get('a.key')]),
      knockout: yA <= yB ? this.hoverBTextKnockout : this.hoverATextKnockout,
      hover: yA <= yB ? this.hoverBText : this.hoverAText,
    };

    // Must set the text before measuring dimensions
    [top, bottom].forEach(function(value){
       console.log(value.raw);
      value.knockout
        .text(value.text)
        .classed('zero', value.raw === 0);
      value.hover
        .text(value.text)
        .classed('zero', value.raw === 0);
    });

    // calculate dimensions
    top.height = top.hover[0][0].offsetHeight;
    bottom.height = bottom.hover[0][0].offsetHeight;

    // Push y-values around to prevent overlap
    if (top.y + top.height >= bottom.y) {
      top.y = bottom.y - bottom.height + 3;
    }

    // Apply y-position
    [top, bottom].forEach(function(value){
      value.knockout
        .transition().duration(50)
        .attr('y', value.y);
      value.hover
        .transition().duration(50)
        .attr('y', value.y);
    });
  },

  transformLabelString: function(value) {
    // overridable
    return value;
  },

  a: function() {
    return this.get('legend')[0];
  }.property('legend'),

  b: function() {
    return this.get('legend')[1];
  }.property('legend')

});

/* Notes from Idan:

L54-L72 this is the crux
you setup an area and a line
and then paths for each using the area / line for data

then L114-115 to actually render it

L94-95
you could set that up in the setup() but I didn’t because it is altered by chart dimensions
you need to set it somewhere before render()
easiest (if static / not responsive) is to just do it wherever you declare your areas

when in doubt, do shit like line { stroke: red; stroke-width: 1; }
area { fill: blue }

    .d3Content {
      fill: none;
 
      .area {
        fill: #eee;
        stroke: none;
        &.light { fill: transparentize($light, 0.7); }
        &.dark { fill: transparentize($dark, 0.7); }
        &.crit { fill: transparentize($crit, 0.5); }
      }
 
      .line {
        stroke: #eee;
        stroke-width: 1;
        &.light { stroke: $light; }
        &.dark { stroke: $dark; }
        &.crit { stroke: $crit; }
      }

*/

