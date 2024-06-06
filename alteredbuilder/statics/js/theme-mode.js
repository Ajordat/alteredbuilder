/*!
 * Color mode toggler for Bootstrap's docs (https://getbootstrap.com/)
 * Copyright 2011-2024 The Bootstrap Authors
 * Licensed under the Creative Commons Attribution 3.0 Unported License.
 */

(() => {
    'use strict'
  
    const getStoredTheme = () => localStorage.getItem('theme')
    const setStoredTheme = theme => localStorage.setItem('theme', theme)
  
    const getPreferredTheme = () => {
      const storedTheme = getStoredTheme()
      if (storedTheme) {
        return storedTheme
      }
  
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }
  
    const setTheme = theme => {
      if (theme === 'auto') {
        theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      }
      document.documentElement.setAttribute('data-bs-theme', theme);
    }
  
    const setTabTheme = theme => {
      if (theme === 'auto') {
        theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      }
      let activeTabElement = document.getElementsByClassName("nav-item border")[0];
      if (!activeTabElement) return;
      if (theme === 'dark') {
        activeTabElement.classList.add("bg-dark");
        activeTabElement.classList.remove("bg-white");
      } else {
        activeTabElement.classList.add("bg-white");
        activeTabElement.classList.remove("bg-dark");
      }
    }
  
    setTheme(getPreferredTheme())
  
    const showActiveTheme = (theme, focus = false) => {
      const themeSwitcher = document.getElementById('bd-theme')
  
      const activeThemeIcon = document.getElementById("theme-icon-active")
      const btnToActive = document.querySelector(`[data-bs-theme-value="${theme}"]`)
      const iconOfActiveBtn = btnToActive.querySelector('i')
  
      document.querySelectorAll('[data-bs-theme-value]').forEach(element => {
        element.classList.remove('active')
        element.setAttribute('aria-pressed', 'false')
      })
  
      btnToActive.classList.add('active')
      btnToActive.setAttribute('aria-pressed', 'true')
      activeThemeIcon.className = iconOfActiveBtn.getAttribute('class')
      const themeSwitcherLabel = `Toggle theme (${btnToActive.dataset.bsThemeValue})`
      themeSwitcher.setAttribute('aria-label', themeSwitcherLabel)
  
      if (focus) {
        themeSwitcher.focus()
      }
    }
  
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      const storedTheme = getStoredTheme()
      if (storedTheme !== 'light' && storedTheme !== 'dark') {
        let theme = getPreferredTheme();
        setTheme(theme)
        showActiveTheme(theme)
        setTabTheme(theme)
      }
    })

    window.addEventListener('DOMContentLoaded', () => {
      let theme = getPreferredTheme();
      showActiveTheme(theme)
      setTabTheme(theme)

      document.querySelectorAll('[data-bs-theme-value]')
        .forEach(toggle => {
          toggle.addEventListener('click', () => {
            const theme = toggle.getAttribute('data-bs-theme-value')
            setStoredTheme(theme)
            setTheme(theme)
            showActiveTheme(theme, true)
            setTabTheme(theme)
          })
        })
    })
  })()
  
  