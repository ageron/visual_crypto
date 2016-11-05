#!/usr/bin/python

from __future__ import division, print_function, unicode_literals

import os
import sys
import random
from PIL import Image
import argparse
import logging

__version__ = "0.1"

def get_options():
    parser = argparse.ArgumentParser(description='Visual cipher image generator.')
    parser.add_argument('--message', '-m',  required = True, metavar = "MESSAGE_IMAGE_FILE_PATH", help='message image')
    parser.add_argument('--secret',  '-s',  metavar = "SECRET_IMAGE_FILE_PATH",    default = "secret.png",   help='secret image (will be created if it does not exist)')
    parser.add_argument('--ciphered', '-c', metavar = "CIPHERED_IMAGE_FILE_PATH", default = "ciphered.png", help='ciphered image (to be generated)')
    parser.add_argument('--resize',  '-r', metavar = "WIDTH,HEIGHT", help='resize message image (defaults to message image size). If width or height is larger than that of the secret image, the secret image will be enlarged appropriately.')
    parser.add_argument('--prepared_message', '-p',  metavar = "PREPARED_MESSAGE_IMAGE_FILE_PATH",  help='if present, the prepared message image is saved to this path')
    parser.add_argument('--display', '-d', action='store_true')
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()
    if args.resize:
        try:
            width, height = [int(i.strip()) for i in args.resize.strip().split(",")]
            args.resize = (width, height)
        except:
            parser.error("Invalid format for resize option.")
        else:
            if width <= 0:
                parser.error("Resize width should be > 0.")
            if height <= 0:
                parser.error("Resize height should be > 0.")
            
    return args

def load_image(name):
    return Image.open(name)

def prepare_message_image(image, size):
    if size != image.size:
        image = image.resize(size, Image.ANTIALIAS)
    return image.convert("1")

def generate_secret(size, secret_image = None):
    width, height = size
    new_secret_image = Image.new(mode = "1", size = (width * 2, height * 2))
    if secret_image:
        old_width, old_height = secret_image.size
    else:
        old_width, old_height = (-1, -1)

    for x in range(0, 2 * width, 2):
        for y in range(0, 2 * height, 2):
            if x < old_width and y < old_height:
                color = secret_image.getpixel((x, y))
            else:
                color = random.getrandbits(1)
            new_secret_image.putpixel((x,  y),   color)
            new_secret_image.putpixel((x+1,y),   1-color)
            new_secret_image.putpixel((x,  y+1), 1-color)
            new_secret_image.putpixel((x+1,y+1), color)
    return new_secret_image

def generate_ciphered_image(secret_image, prepared_image):
    width, height = prepared_image.size
    ciphered_image = Image.new(mode = "1", size = (width * 2, height * 2))
    for x in range(0, width*2, 2):
        for y in range(0, height*2, 2):
            secret = secret_image.getpixel((x,y))
            message = prepared_image.getpixel((x/2,y/2))
            if (message > 0 and secret > 0) or (message == 0 and secret == 0):
                color = 0
            else:
                color = 1
            ciphered_image.putpixel((x,  y),   1-color)
            ciphered_image.putpixel((x+1,y),   color)
            ciphered_image.putpixel((x,  y+1), color)
            ciphered_image.putpixel((x+1,y+1), 1-color)
    return ciphered_image

def main():
    logging.basicConfig()

    args = get_options()
    if args.verbose > 2:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose > 1:
        logging.getLogger().setLevel(logging.INFO)
    elif args.verbose > 0:
        logging.getLogger().setLevel(logging.WARNING)
    else:
        logging.getLogger().setLevel(logging.ERROR)

    logging.info("Cipher image generator version %s" % __version__)

    try:
        logging.debug("Loading message image '%s'" % (args.message))
        message_image = load_image(args.message)
    except IOError as e:
        logging.fatal("Fatal error: I/O error while loading message image '%s' (%s)" % (args.message, str(e)))
        sys.exit(1)

    if args.resize is None:
        size = message_image.size
    else:
        size = args.resize
    
    width, height = size
    
    save_secret = False
    
    if os.path.isfile(args.secret):
        try:
            logging.debug("Loading secret image '%s'" % (args.secret))
            secret_image = load_image(args.secret)
            secret_width, secret_height = secret_image.size
            if secret_width < width or secret_height < height:
                logging.info("Enlarging secret image to fit message size")
                secret_image = generate_secret(size, secret_image = secret_image)
                save_secret = True
        except IOError:
            logging.fatal("I/O error while loading secret image '%s' (%s)" % (args.secret, str(e)))
            sys.exit(2)
    else:
        logging.info("Generating secret image '%s'" % (args.secret))
        secret_image = generate_secret(size)
        save_secret = True

    prepared_image = prepare_message_image(message_image, size)
    ciphered_image = generate_ciphered_image(secret_image, prepared_image)
    
    if save_secret:
        logging.debug("Saving secret image '%s'" % (args.secret))
        try:
            secret_image.save(args.secret)
        except IOError as e:
            logging.error("I/O error while saving secret image '%s' (%s)" % (args.secret, str(e)))
    
    if args.prepared_message:
        logging.debug("Saving prepared message image '%s'" % (args.prepared_message))
        try:
            prepared_image.save(args.prepared_message)
        except IOError as e:
            logging.error("I/O error while saving prepared message image '%s' (%s)" % (args.prepared_message, str(e)))
    
    try:
        ciphered_image.save(args.ciphered)
    except IOError as e:
        logging.fatal("I/O error while saving ciphered image '%s' (%s)" % (args.ciphered, str(e)))
        sys.exit(3)

    if args.display:
        prepared_image.show()
        secret_image.show()
        ciphered_image.show()

if __name__ == '__main__':
    main()
