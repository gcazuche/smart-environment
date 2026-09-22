import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = readFileSync(new URL("../../app/web/static/web/login.js", import.meta.url), "utf8");

class Element {
  hidden = false;
}

class Button extends Element {
  hidden = true;
  textContent = "Ocultar detalhes de acesso";
  attributes = new Map([["aria-expanded", "true"]]);
  listeners = new Map();
  getAttribute(key) { return this.attributes.get(key); }
  setAttribute(key, value) { this.attributes.set(key, value); }
  addEventListener(event, listener) { this.listeners.set(event, listener); }
  click() { this.listeners.get("click")(); }
}

function run(toggle, details) {
  vm.runInNewContext(source, {
    HTMLButtonElement: Button,
    HTMLElement: Element,
    document: { getElementById: (id) => id === "migration-toggle" ? toggle : details },
  });
}

test("details remain readable initially, then toggle with matching ARIA", () => {
  const toggle = new Button();
  const details = new Element();
  run(toggle, details);
  assert.equal(toggle.hidden, false);
  assert.equal(details.hidden, false);
  toggle.click();
  assert.equal(details.hidden, true);
  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  assert.equal(toggle.textContent, "Ver detalhes de acesso");
  toggle.click();
  assert.equal(details.hidden, false);
  assert.equal(toggle.getAttribute("aria-expanded"), "true");
  assert.equal(toggle.textContent, "Ocultar detalhes de acesso");
});

test("script tolerates pages without migration elements", () => {
  assert.doesNotThrow(() => run(null, null));
  assert.doesNotThrow(() => run(new Element(), new Element()));
  assert.doesNotThrow(() => run(new Button(), null));
});
