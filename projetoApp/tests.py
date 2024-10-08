from django.test import TestCase
from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import LiveServerTestCase
from selenium import webdriver
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .models import Evento, CustomUser
import datetime

class CustomUserManagerTest(TestCase):
    def setUp(self):
        self.manager = get_user_model().objects

    def test_create_user(self):
        email = "test@example.com"
        password = "password123"
        user = self.manager.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        email = "admin@example.com"
        password = "adminpassword"
        superuser = self.manager.create_superuser(email=email, password=password)

        self.assertEqual(superuser.email, email)
        self.assertTrue(superuser.check_password(password))
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_create_superuser_invalido(self):
        email = "admin@example.com"
        password = "adminpassword"

        with self.assertRaises(ValueError):
            self.manager.create_superuser(email=email, password=password, is_staff=False)

        with self.assertRaises(ValueError):
            self.manager.create_superuser(email=email, password=password, is_superuser=False)

class EventoManagerTest(TestCase):
    def setUp(self):
        self.evento_manager = Evento.objects

    def test_get_home_event_futuro(self):
        future_date = datetime.date.today() + datetime.timedelta(days=7)
        event = Evento.objects.create(data=future_date, ativo=True)

        home_event = self.evento_manager.get_home_event()

        self.assertEqual(home_event, event)

    def test_get_home_event_passado(self):
        past_date = datetime.date.today() - datetime.timedelta(days=7)
        event = Evento.objects.create(data=past_date, ativo=True)

        home_event = self.evento_manager.get_home_event()

        self.assertEqual(home_event, event)

    def test_get_home_event_vazio(self):
        with self.assertRaises(Http404):
            self.evento_manager.get_home_event()

    def test_get_home_event_inativo(self):
        past_date = datetime.date.today() - datetime.timedelta(days=7)
        Evento.objects.create(data=past_date, ativo=False)

        with self.assertRaises(Http404):
            self.evento_manager.get_home_event()

class TesteLoginSelenium(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        service = Service(EdgeChromiumDriverManager().install())
        cls.selenium = webdriver.Edge(service=service)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.email = 'email@email.com'
        self.password = 'senha'
        self.user = CustomUser.objects.create_user(email=self.email, password=self.password)

    def test_login(self):
        self.selenium.get(self.live_server_url + '/login/')

        username_input = self.selenium.find_element(By.ID, 'id_username')
        password_input = self.selenium.find_element(By.ID, 'id_password')

        username_input.send_keys(self.email)
        password_input.send_keys(self.password)

        password_input.send_keys(Keys.RETURN)

        self.ass.get(self.live_server_url + '/')
