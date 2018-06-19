Threat Model
============

The Metadata Anonymisation Toolkit 2 adversary has a number
of goals, capabilities, and counter-attack types that can be
used to guide us towards a set of requirements for the MAT2.

This is an overhaul of MAT's (the first iteration of the software) one.

Warnings
--------

Mat only removes standard metadata from your files, it does _not_:

  - anonymise their content (the substance and the form)
  - handle watermarking
  - handle steganography nor homoglyphs
  - handle stylometry
  - handle any non-standard metadata field/system
  - handle file-system related metadata

If you really want to be anonymous format that does not contain any
metadata, or better : use plain-text ASCII without trailing spaces.

And as usual, think twice before clicking.


Adversary
---------

* Goals:

    - Identifying the source of the document, since a document
    always has one. Who/where/when/how was a picture
    taken, where was the document leaked from and by
    whom, ...

    - Identify the author; in some cases documents may be
    anonymously authored or created. In these cases,
    identifying the author is the goal.

    - Identify the equipment/software used. If the attacker fails
    to directly identify the author and/or source, his next
    goal is to determine the source of the equipment used
    to produce, copy, and transmit the document. This can
    include the model of camera used to take a photo or a film, 
    which software was used to produce an office document, …


* Adversary Capabilities - Positioning

    - The adversary created the document specifically for this
    user. This is the strongest position for the adversary to
    have. In this case, the adversary is capable of inserting
    arbitrary, custom watermarks specifically for tracking
    the user. In general, MAT2 cannot defend against this
    adversary, but we list it for completeness' sake.

    - The adversary created the document for a group of users.
    In this case, the adversary knows that they attempted to
    limit distribution to a specific group of users. They may
    or may not have watermarked the document for these
    users, but they certainly know the format used.

		- The adversary did not create the document, the weakest
		position for the adversary to have. The file format is
		(most of the time) standard, nothing custom is added:
		MAT2 must be able to remove all metadata from the file.


Requirements
------------

* Processing

    - MAT2 *should* avoid interactions with information.
    Its goal is to remove metadata, and the user is solely
    responsible for the information of the file.

    - MAT2 *must* warn when encountering an unknown
    format. For example, in a zipfile, if MAT encounters an
    unknown format, it should warn the user, and ask if the
    file should be added to the anonymised archive that is
    produced.

    - MAT2 *must* not add metadata, since its purpose is to
    anonymise files: every added items of metadata decreases
    anonymity.

    - MAT2 *should* handle unknown/hidden metadata fields,
    like proprietary extensions of open formats.

		- MAT2 *must not* fail silently. Upon failure,
		MAT2 *must not* modify the file in any way.

		- MAT2 *might* leak the fact that MAT2 was used on the file,
		since it might be uncommon for some file formats to come
		without any kind of metadata, an adversary might suspect that
		the user used MAT2 on certain files.

