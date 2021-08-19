Static Assets
=============

This directory contains the static assets used by Patchwork. Many of these are
third-party, though there are some are custom assets in there.


.. _css:

css
---

``bootstrap.min.css``
  CSS for the `Bootstrap` library.

  Refer to the :ref:`js` section below for more information on `Bootstrap`.

``selectize.bootstrap3.css``
  CSS for the `Selectize` library.

  Refer to the :ref:`js` section below for more information on `Selectize`.

``style.css``
  Custom, Patchwork styling. Mostly a collection of overrides for default
  Bootstrap styles.

  Part of Patchwork.


.. _fonts:

fonts
-----

``glyphicons-halflings-regular.*``
  Library of precisely prepared monochromatic icons and symbols, created with
  an emphasis to simplicity and easy orientation. Provided as part of the
  Bootstrap library.

  These are in multiple formats to support different browsers/environments.
  Refer to the :ref:`js` section below for more information on Bootstrap.


.. _js:

js
--

``bootstrap.js``
  The most popular HTML, CSS, and JavaScript framework for developing
  responsive, mobile first projects on the web.

  This is used for the main UI of Patchwork.

  :Website: https://getbootstrap.com/
  :GitHub: https://github.com/twbs/bootstrap/
  :Version: 3.2.0

``bundle.js``
  Utility functions for bundle patch list manipulation (re-ordering patches,
  etc.)

  Part of Patchwork.

``clipboard.min.js``
  Modern copy to clipboard. No Flash. Just 3kb gzipped

  This is used to allow us to "click to copy" various elements in the UI.

  :Website: https://clipboardjs.com/
  :GitHub: https://github.com/zenorocha/clipboard.js/
  :Version: 1.7.1

``jquery.js``
  jQuery is a fast, small, and feature-rich JavaScript library. It makes things
  like HTML document traversal and manipulation, event handling, animation, and
  Ajax much simpler with an easy-to-use API that works across a multitude of
  browsers. With a combination of versatility and extensibility, jQuery has
  changed the way that millions of people write JavaScript.

  This is used across Patchwork, including by the likes of ``bundle.js``, as
  well as by the various plugins below.

  :Website: https://jquery.com/
  :GitHub: https://github.com/jquery/jquery
  :Version: 1.10.1

``jquery.checkboxes.js``
  A jQuery plugin that gives you nice powers over your checkboxes.

  This is used to allow shift-select of checkboxes on the patch list page.

  :Website: http://rmariuzzo.github.io/checkboxes.js
  :GitHub: https://github.com/rmariuzzo/checkboxes.js
  :Version: 1.0.6

``jquery.stickytableheaders.js``
  A jQuery plugin that makes large tables more usable by having the table
  header stick to the top of the screen when scrolling.

  This is used to ensure the heads on the patch list page stay at the top as we
  scroll.

  :GitHub: https://github.com/jmosbech/StickyTableHeaders
  :Version: 0.1.19

``jquery.tablednd.js``
  jQuery plug-in to drag and drop rows in HTML tables.

  This is used by the bundle patch list to allow us to control the order of the
  patches in said bundle.

  :Website: http://www.isocra.com/2008/02/table-drag-and-drop-jquery-plugin/
  :GitHub: jQuery plug-in to drag and drop rows in HTML tables
  :Version: ???

``js.cookie.min.js``
  Library used to handle cookies.

  This is used to get the ``csrftoken`` cookie for AJAX requests in JavaScript.

  :GitHub: https://github.com/js-cookie/js-cookie/
  :Version: 3.0.0

``rest.js.``
  Utility module for REST API requests to be used by other Patchwork JS files.

  Part of Patchwork.

``selectize.min.js``
  Selectize is the hybrid of a ``textbox`` and ``<select>`` box. It's jQuery
  based and it has autocomplete and native-feeling keyboard navigation; useful
  for tagging, contact lists, etc.

  :Website: https://selectize.github.io/selectize.js/
  :GitHub: https://github.com/selectize/selectize.js
  :Version: 0.11.2
