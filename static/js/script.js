
  let navbar = document.querySelector('.navbar');

  console.log('Script file loaded successfully.');

  document.querySelector('#menu-btn').onclick = () =>{
    navbar.classList.toggle('active');
    console.log('Script file loaded successfully1.');
  }


document.querySelector('#close-navbar').onclick = () =>{
  navbar.classList.remove('active');
}

let searchForm = document.querySelector('.search-form');

document.querySelector('#search-btn').onclick = () =>{
  searchForm.classList.toggle('active');
};

window.onscroll = () =>{
  navbar.classList.remove('active');
  searchForm.classList.remove('active');
};

let slides = document.querySelectorAll('.home .slide');
let index = 0;

function next(){
  slides[index].classList.remove('active');
  index = (index + 1) % slides.length;
  slides[index].classList.add('active');
}

function prev(){
  slides[index].classList.remove('active');
  index = (index - 1 + slides.length) % slides.length;
  slides[index].classList.add('active');
};

var swiper = new Swiper(".products-slider", {
  loop: true,
  grabCursor : true,
  spaceBetween: 20,
  navigation: {
    nextEl: ".swiper-button-next",
    prevEl: ".swiper-button-prev",
  },
  breakpoints: {
    0: {
      slidesPerView: 1,
    },
    550: {
      slidesPerView: 2,
    },
    850: {
      slidesPerView: 3,
    },
    1200: {
      slidesPerView: 4,
    },
  },
});

var swiper = new Swiper(".arrivals-slider", {
  loop: true,
  grabCursor : true,
  spaceBetween: 20,
  navigation: {
    nextEl: ".swiper-button-next",
    prevEl: ".swiper-button-prev",
  },
  breakpoints: {
    0: {
      slidesPerView: 1,
    },
    550: {
      slidesPerView: 2,
    },
    850: {
      slidesPerView: 3,
    },
    1200: {
      slidesPerView: 4,
    },
  },
});

var swiper = new Swiper(".reviews-slider", {
  loop: true,
  grabCursor : true,
  spaceBetween: 20,
  breakpoints: {
    0: {
      slidesPerView: 1,
    },
    768: {
      slidesPerView: 2,
    },
    991: {
      slidesPerView: 3,
    },
  },
});

var swiper = new Swiper(".blogs-slider", {
  loop: true,
  grabCursor : true,
  spaceBetween: 20,
  navigation: {
    nextEl: ".swiper-button-next",
    prevEl: ".swiper-button-prev",
  },
  breakpoints: {
    0: {
      slidesPerView: 1,
    },
    650: {
      slidesPerView: 2,
    },
    1200: {
      slidesPerView: 3,
    },
  },
});
const addToCartBtn = document.getElementById('add-to-cart-btn');
const cartCounter = document.getElementById('cart-counter');

addToCartBtn.addEventListener('click', () => {
  cartCounter.style.display = 'inline-block';
  if (cartCounter.textContent === '') {
    cartCounter.textContent = 1;
  } else {
    let cartCount = parseInt(cartCounter.textContent);
    cartCount++;
    cartCounter.textContent = cartCount;
  }
});

var heartIcon = document.querySelectorAll('.fa-heart');
var likesCounter = document.querySelector("#likes-counter");

likesCounter.style.display = 'inline-block';
for (let i = 0; i < heartIcon.length; i++) {
    heartIcon[i].addEventListener("click", function()  {
        likesCounter.style.display = 'inline-block';
        var currentLikes = parseInt(likesCounter.textContent);
        likesCounter.textContent = currentLikes + 1;
    });
}

const ratings = document.querySelectorAll('.rating input');

ratings.forEach(radio => {
  radio.addEventListener('click', () => {
    console.log('User selected rating:', radio.value);
  });
});
