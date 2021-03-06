#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import VenueForm, ArtistForm, ShowForm
from flask_migrate import Migrate
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# FINISHED: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='Venue', lazy=True)
    past_count = db.Column(db.Integer)
    future_count = db.Column(db.Integer)
    genres = db.Column(db.ARRAY(db.String))

    # FINISHED: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref="Artist", lazy=True)
    past_count = db.Column(db.Integer)
    future_count = db.Column(db.Integer)

    # FINISHED: implement any missing fields, as a database migration using Flask-Migrate

# FINISHED Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime(), default=datetime.utcnow)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', ondelete='CASCADE'))
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', ondelete='CASCADE'))

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # FINISHED: replace with real venues data.
  # num_shows should be aggregated based on number of upcoming shows per venue.
  return render_template('pages/venues.html', venue=Venue.query.order_by(Venue.city).all(), cities=Venue.query.distinct(Venue.city))

@app.route('/venues/search', methods=['POST'])
def search_venues():

  # FINISHED: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term=request.form.get('search_term', '')
  venues = db.session.query(Venue).filter(Venue.name.ilike('%' + search_term + '%')).all()
  searched_data = []
  for venue in venues:
    num_upcoming_shows = 0
    shows = db.session.query(Show).filter(Show.venue_id == venue.id)
    for show in shows:
      if (str(show.start_time) > str(datetime.now())):
        num_upcoming_shows += 1
    searched_data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": num_upcoming_shows
    })
  response = {
    "count": len(venues),
    "data": searched_data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # FINISHED: replace with real venue data from the venues table, using venue_id  --FIX GENRE VIEW--
  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  past_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
    filter(Show.venue_id == venue.id, Show.artist_id == Artist.id, Show.start_time < datetime.now()).all()
  upcoming_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
    filter(Show.venue_id == venue.id, Show.artist_id == Artist.id, Show.start_time > datetime.now()).all()
  data = {
    'id': venue.id,
    "name": venue.name,
    "city": venue.city,
    "state": venue.state,
    "address": venue.address,
    "phone": venue.phone,
    "image_link": venue.image_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "genres": venue.genres,
    "website_link": venue.website_link,
    "upcoming_shows": [{
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link, 
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")} 
      for artist,show in upcoming_shows],
    "past_shows": [{
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link, 
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")} 
      for artist,show in past_shows],
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # FINISHED: insert form data as a new Venue record in the db, instead
  # FINISHED: modify data to be the data object returned from db insertion
  # on successful db insert, flash success
  error = False
  form = VenueForm()
  try:
    venue = Venue(
      name=request.form['name'], 
      city=request.form['city'], 
      state=request.form['state'], 
      address=request.form['address'],
      phone=request.form['phone'], 
      genres=request.form.getlist('genres'), 
      facebook_link=request.form['facebook_link'], 
      image_link=request.form['image_link'],
      seeking_talent=request.form['seeking_talent'], 
      seeking_description=request.form['seeking_description'], 
      website_link=request.form['website_link'])
    if (venue.seeking_talent == 'y'):
      venue.seeking_talent = True
    else:
      venue.seeking_talent = False
    db.session.add(venue)
  except:
    error = True
  finally:
    if not error:
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    else:
      # FINISHED: on unsuccessful db insert, flash an error instead.
      # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      flash('An error occured. Venue' + venue.name + 'could not be listed.')
      db.session.rollback()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    flash('An error occured. Venue' + venue.name + 'could not be deleted.')
    db.session.rollback()
  finally:
    db.session.close()
  # FINISHED: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # FINISHED: replace with real data returned from querying the database
  return render_template('pages/artists.html', artists=Artist.query.order_by(Artist.name).all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # FINISHED: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term=request.form.get('search_term', '')
  artists = db.session.query(Artist).filter(Artist.name.ilike('%' + search_term + '%')).all()
  searched_data = []
  for artist in artists:
    num_upcoming_shows = 0
    shows = db.session.query(Show).filter(Show.artist_id == artist.id)
    for show in shows:
      if (str(show.start_time) > str(datetime.now())):
        num_upcoming_shows += 1
    searched_data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": num_upcoming_shows
    })
  response = {
    "count": len(artists),
    "data": searched_data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # FINISHED: replace with real venue data from the venues table, using venue_id
  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  past_shows = db.session.query(Venue, Show).join(Show).join(Artist).\
    filter(Show.artist_id == artist.id, Show.venue_id == Venue.id, Show.start_time < datetime.now()).all()
  upcoming_shows = db.session.query(Venue, Show).join(Show).join(Artist).\
    filter(Show.artist_id == artist.id, Show.venue_id == Venue.id, Show.start_time > datetime.now()).all()
  data = {
    'id': artist.id,
    "name": artist.name,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "image_link": artist.image_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "genres": artist.genres,
    "website_link": artist.website_link,
    "upcoming_shows": [{
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link, 
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")} 
      for venue,show in upcoming_shows],
    "past_shows": [{
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link, 
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")} 
      for venue,show in past_shows],
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website_link": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }
  # FINISHED: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  artist = Artist.query.get(artist_id)
  error = False
  try:
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form['facebook_link']
    artist.website_link = request.form['website_link']
    artist.seeking_description = request.form['seeking_description']
    artist.image_link = request.form['image_link']
    artist.seeking_venue = request.form['seeking_venue']
    if (artist.seeking_venue == 'y'):
      setattr(artist, 'seeking_venue', True)
    else:
      setattr(artist, 'seeking_venue', False)
  except:
    error = True
  finally:
    if not error:
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
    else:
      flash('An error occured. Artist ' + artist.name + ' could not be updated.')
      db.session.rollback()
  # FINISHED: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website_link": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "address": venue.address
  }
  # FINISHED: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  venue = Venue.query.get(venue_id)
  error = False
  try:
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form['facebook_link']
    venue.website_link = request.form['website_link']
    venue.seeking_description = request.form['seeking_description']
    venue.image_link = request.form['image_link']
    venue.seeking_talent = request.form['seeking_talent']
    venue.address = request.form['address']
    if (venue.seeking_talent == 'y'):
      setattr(venue, 'seeking_talent', True)
    else:
      setattr(venue, 'seeking_talent', False)
  except:
    error = True
  finally:
    if not error:
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully updated!')
    else:
      flash('An error occured. Venue ' + venue.name + ' could not be updated.')
      db.session.rollback()
  # FINISHED: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # FINISHED: insert form data as a new Artist record in the db, instead
  # FINISHED: modify data to be the data object returned from db insertion
  error = False
  form = ArtistForm()
  try:
    artist = Artist(
      name=request.form['name'], 
      city=request.form['city'], 
      state=request.form['state'],
      phone=request.form['phone'], 
      genres=request.form.getlist('genres'), 
      facebook_link=request.form['facebook_link'], 
      image_link=request.form['image_link'],
      seeking_venue=request.form['seeking_venue'], 
      seeking_description=request.form['seeking_description'], 
      website_link=request.form['website_link'])
    if (artist.seeking_venue == 'y'):
      artist.seeking_venue = True
    else:
      artist.seeking_venue = False
    db.session.add(artist)
  except:
    error = True
  finally:
    if not error:
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    else:
      # FINISHED: on unsuccessful db insert, flash an error instead.
      # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      flash('An error occured. Artist' + artist.name + 'could not be listed.')
      db.session.rollback()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # FINISHED: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  shows = Show.query.order_by(Show.start_time.desc()).all()
  data = []
  for show in shows:
    venue = Venue.query.filter_by(id=show.venue_id).first_or_404()
    artist = Artist.query.filter_by(id=show.artist_id).first_or_404()
    data.extend([{
    "venue_id": venue.id,
    "venue_name": venue.name,
    "artist_id": artist.id,
    "artist_name": artist.name,
    "artist_image_link": artist.image_link,
    "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
  }])
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  form = ShowForm()
  try:
    show = Show(
      venue_id=request.form['venue_id'],
      artist_id=request.form['artist_id'],
      start_time=request.form['start_time']) 
    db.session.add(show)
  except:
    error = True
  finally:
    if not error:
      db.session.commit()
      # on successful db insert, flash success
      flash('Show was successfully listed!')
    else:
      # FINISHED: on unsuccessful db insert, flash an error instead.
      # e.g., flash('An error occurred. Show could not be listed.')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      flash('An error occured. Show could not be listed.')
      db.session.rollback()
  # called to create new shows in the db, upon submitting new show listing form
  # FINISHED: insert form data as a new Show record in the db, instead
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.testing=True
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
