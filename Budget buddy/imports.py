import sqlite3
import os
from io import BytesIO
import base64
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from openai import OpenAI
from PIL import Image
import database
import re
import json
from InvoiceClass import Invoice
from pydub import AudioSegment
import tempfile

