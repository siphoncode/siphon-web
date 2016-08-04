'use strict';

import 'es5-shim' // for IE8 compatibility
import React from 'react'
import { render } from 'react-dom'
import $ from 'jquery'
import moment from 'moment'
import './jquery-csrf-fix'

var AppTile = React.createClass({
  handleDelete(e) {
    if (confirm('Are you sure you want to delete this app?') == true) {
      var url = '/api/v1/apps/' + this.props.id;
      $.ajax({
        url: url,
        type: 'DELETE',
        success: function() {
          this.props.reload();
        }.bind(this),
        error: function(xhr, status, err) {
          alert(err.toString());
        }.bind(this)
      });
    }
    e.preventDefault();
  },
  render() {
    return (
      <div className="dashboard__tile" key={this.props.id}>
        <div className="dashboard__tile__status"><span /></div>
        <div className="dashboard__tile__icon" />
        <div className="dashboard__tile__text">
          <span className="dashboard__tile__name">{this.props.name}</span>
          <span className="dashboard__tile__blurb">
            last pushed {this.props.lastUpdated}
            <span> | </span>
            <a href="#" onClick={this.handleDelete}>delete</a>
          </span>
        </div>
      </div>
    )
  }
})

var AppTiles = React.createClass({
  render() {
    var tiles = this.props.apps.map((app) => {
      var lastUpdated = moment(app.last_updated).fromNow()
      return <AppTile key={app.id} id={app.id} name={app.name}
        lastUpdated={lastUpdated} reload={this.props.reload} />
    })
    var noApps = (
      <div className="dashboard__tiles__empty">
        <img src="/static/img/dashboard/spinner.gif" width="24" height="24" />
        <span>No apps created yet.</span>
      </div>
    )
    return (
      <div className="dashboard__tiles">
        {tiles.length > 0 ? tiles : noApps}
      </div>
    )
  }
})

var Dashboard = React.createClass({
  getInitialState() {
    return {apps: []};
  },
  onReload() {
    this.setState({apps: []});
    this._load();
  },
  _load() {
    var url = '/api/v1/apps/';
    $.ajax({
      url: url,
      dataType: 'json',
      cache: false,
      success: function(obj) {
        this.setState({apps: obj.results});
        setTimeout(function() {
          this._load();
        }.bind(this), 5000)
      }.bind(this),
      error: function(xhr, status, err) {
        console.error(url, status, err.toString());
      }.bind(this)
    });
  },
  componentDidMount() {
      this._load();
  },
  render() {
    return (
      <div>
        <div className="dashboard__subheading">Your apps</div>
        <AppTiles apps={this.state.apps} reload={this.onReload} />
      </div>
    )
  }
})

render(<Dashboard />, document.getElementById('dashboard-app'));
