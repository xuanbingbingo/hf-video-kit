/**
 * animation-utils.js — Remotion 动效精华移植 GSAP/hf-video-kit
 *
 * ⚠️ 使用方法：把本文件完整内联到 index.html <script> 块
 *    （禁止 <script src> 外链，headless Chrome 会因 MIME 识别问题拒绝执行，
 *    导致所有 remotion.* ease 未注册，渲染全黑。
 *    参考：examples/remotion-style-demo/landscape/index.html）
 *
 * 四条注册 ease（内联后即可在任意 tween 中使用）：
 *   remotion.snappy  bezier(0.16,1,0.3,1)       UI 快速入场
 *   remotion.spring  bezier(0.34,1.56,0.64,1)   弹簧过冲
 *   remotion.easeIn  bezier(0.32,0,0.67,0)      退场加速
 *   remotion.smooth  bezier(0.45,0,0.55,1)      平滑过渡
 *
 * 30 个 AnimUtils 函数（window.AnimUtils.xxx）：
 *
 * 【数据可视化 10 个】
 *   counter            数字累加器（从 N 计到 M）
 *   barGrow            横向柱状图（scaleX 生长）
 *   barGrowVertical    竖向柱状图（scaleY 从底部生长）
 *   lineChart          折线图路径描绘（stroke-dashoffset）
 *   areaChart          面积图（折线 + 填充区渐显）
 *   donutProgress      圆环/甜甜圈进度（SVG circle）
 *   bubbleChart        气泡图（scale 弹出）
 *   heatGrid           热力格子（逐格淡入）
 *   flipCounter        翻牌数字（rotateX 翻转）
 *   isotype            人形图（高亮前 N 个）
 *
 * 【文字动效 7 个】
 *   staggerIn          批量交错入场（通用）
 *   charReveal         逐字揭示（支持关键词金色高亮）
 *   wordReveal         整词入场（空格分词）
 *   typewriter         打字机 + 光标
 *   highlightSweep     高亮扫线（半透明色块从左划过）
 *   morphText          文字溶解变形（blur 渐隐渐显切词）
 *   lineSlideIn        行文字从左推入
 *
 * 【UI 组件 6 个】
 *   cardSpring         卡片弹出（spring 过冲）
 *   progressBar        进度条填充
 *   progressRing       圆形进度环
 *   timelineNodes      时间轴节点（竖线生长 + 节点弹出）
 *   tagPop             标签/Tag 弹出
 *   chatBubbles        对话气泡（左右交替入场）
 *
 * 【氛围效果 7 个】
 *   ripplePulse        涟漪脉冲（向外扩散圆环）
 *   pathDraw           SVG 路径描绘
 *   colorMorph         颜色插值过渡
 *   shimmer            扫光（斜向高光条）
 *   particleBurst      粒子爆出（8 点散射）
 *   cardFlip3D         3D 翻转卡
 *   gradientFlow       背景渐变漂移（双向往返，无 repeat）
 */
(function () {
  if (typeof gsap === "undefined") return;

  /* ─────────────────────── Bezier 求解器（Newton-Raphson）─────────────────────── */
  function cubicBezier(p1x, p1y, p2x, p2y) {
    var NI = 8, NMS = 0.001, SP = 1e-7, SMI = 10, kSTS = 11, kSSS = 1.0 / (kSTS - 1.0);
    function A(a1, a2) { return 1.0 - 3.0 * a2 + 3.0 * a1; }
    function B(a1, a2) { return 3.0 * a2 - 6.0 * a1; }
    function C(a1) { return 3.0 * a1; }
    function calcBezier(t, a1, a2) { return ((A(a1, a2) * t + B(a1, a2)) * t + C(a1)) * t; }
    function getSlope(t, a1, a2) { return 3.0 * A(a1, a2) * t * t + 2.0 * B(a1, a2) * t + C(a1); }
    var sv = new Float32Array(kSTS);
    if (p1x !== p1y || p2x !== p2y) {
      for (var i = 0; i < kSTS; ++i) sv[i] = calcBezier(i * kSSS, p1x, p2x);
    }
    function getTForX(aX) {
      var is = 0.0, cs = 1, ls = kSTS - 1;
      for (; cs !== ls && sv[cs] <= aX; ++cs) is += kSSS;
      --cs;
      var dist = (aX - sv[cs]) / (sv[cs + 1] - sv[cs]);
      var gft = is + dist * kSSS;
      var isl = getSlope(gft, p1x, p2x);
      if (isl >= NMS) {
        for (var j = 0; j < NI; ++j) {
          var csl = getSlope(gft, p1x, p2x);
          if (csl === 0.0) return gft;
          gft -= (calcBezier(gft, p1x, p2x) - aX) / csl;
        }
        return gft;
      } else if (isl === 0.0) { return gft; }
      var aA = is, aB = is + kSSS, k = 0, cX, cT;
      do {
        cT = aA + (aB - aA) / 2.0;
        cX = calcBezier(cT, p1x, p2x) - aX;
        if (cX > 0.0) aB = cT; else aA = cT;
      } while (Math.abs(cX) > SP && ++k < SMI);
      return cT;
    }
    return function (p) {
      if (p1x === p1y && p2x === p2y) return p;
      if (p === 0 || p === 1) return p;
      return calcBezier(getTForX(p), p1y, p2y);
    };
  }
  function reg(name, p1x, p1y, p2x, p2y) { gsap.registerEase(name, cubicBezier(p1x, p1y, p2x, p2y)); }
  reg("remotion.snappy", 0.16, 1,    0.3,  1);
  reg("remotion.spring", 0.34, 1.56, 0.64, 1);
  reg("remotion.easeIn", 0.32, 0,    0.67, 0);
  reg("remotion.smooth", 0.45, 0,    0.55, 1);

  /* 注入光标闪烁 CSS（幂等） */
  if (!document.getElementById("au-style")) {
    var s = document.createElement("style");
    s.id = "au-style";
    s.textContent = "@keyframes auBlink{0%,100%{opacity:1}50%{opacity:0}}";
    document.head.appendChild(s);
  }

  /* ─────────────────────── AnimUtils ─────────────────────── */
  window.AnimUtils = {

    /* ══════════════════════════════════════════════════════════
     * 数据可视化
     * ══════════════════════════════════════════════════════════ */

    /**
     * 数字累加器 — el.textContent 从 from 计到 to
     * @param {Element} el
     * @param {number}  from
     * @param {number}  to
     * @param {number}  duration  秒
     * @param {string}  ease      默认 remotion.snappy
     * @param {object}  tl        GSAP Timeline
     * @param {number}  at        插入时间
     * @param {string}  suffix    后缀，如 "%"、"万"
     */
    counter: function (el, from, to, duration, ease, tl, at, suffix) {
      ease = ease || "remotion.snappy";
      suffix = suffix || "";
      var obj = { val: from };
      var decimals = (String(to).split(".")[1] || "").length;
      var props = {
        val: to, duration: duration, ease: ease,
        onUpdate: function () { el.textContent = obj.val.toFixed(decimals) + suffix; },
        onComplete: function () { el.textContent = to.toFixed(decimals) + suffix; }
      };
      tl ? tl.to(obj, props, at) : gsap.to(obj, props);
    },

    /**
     * 横向柱状图 — .bar-fill 元素 scaleX:0→1
     * opts: duration, stagger, ease
     */
    barGrow: function (selector, tl, at, opts) {
      opts = opts || {};
      var dur = opts.duration || 0.6;
      var stagger = opts.stagger !== undefined ? opts.stagger : 0.12;
      var ease = opts.ease || "remotion.snappy";
      gsap.utils.toArray(selector).forEach(function (el, i) {
        tl.fromTo(el,
          { scaleX: 0, transformOrigin: "left center" },
          { scaleX: 1, duration: dur, ease: ease },
          at + i * stagger);
      });
    },

    /**
     * 竖向柱状图 — 从底部生长 scaleY:0→1
     * opts: duration, stagger, ease, labelSelector（柱顶标签）
     */
    barGrowVertical: function (selector, tl, at, opts) {
      opts = opts || {};
      var dur = opts.duration || 0.65;
      var stagger = opts.stagger !== undefined ? opts.stagger : 0.1;
      var ease = opts.ease || "remotion.snappy";
      var labels = opts.labelSelector ? gsap.utils.toArray(opts.labelSelector) : [];
      gsap.utils.toArray(selector).forEach(function (el, i) {
        tl.fromTo(el,
          { scaleY: 0, transformOrigin: "center bottom" },
          { scaleY: 1, duration: dur, ease: ease },
          at + i * stagger);
        if (labels[i]) {
          tl.fromTo(labels[i],
            { opacity: 0, y: 10 },
            { opacity: 1, y: 0, duration: 0.3, ease: "remotion.snappy" },
            at + i * stagger + dur - 0.15);
        }
      });
    },

    /**
     * 折线图 — SVG <path> 描线（stroke-dashoffset）
     * opts: duration, ease
     */
    lineChart: function (pathEl, tl, at, opts) {
      opts = opts || {};
      var dur = opts.duration || 1.2;
      var ease = opts.ease || "remotion.smooth";
      var len = (pathEl.getTotalLength && pathEl.getTotalLength()) || 500;
      gsap.set(pathEl, { strokeDasharray: len, strokeDashoffset: len });
      tl.to(pathEl, { strokeDashoffset: 0, duration: dur, ease: ease }, at);
    },

    /**
     * 面积图 — 折线描出 + 填充区域渐显
     * opts: duration, ease
     */
    areaChart: function (pathEl, fillEl, tl, at, opts) {
      opts = opts || {};
      var dur = opts.duration || 1.2;
      var ease = opts.ease || "remotion.smooth";
      var len = (pathEl.getTotalLength && pathEl.getTotalLength()) || 500;
      gsap.set(pathEl, { strokeDasharray: len, strokeDashoffset: len });
      tl.to(pathEl, { strokeDashoffset: 0, duration: dur, ease: ease }, at);
      if (fillEl) {
        gsap.set(fillEl, { opacity: 0 });
        tl.to(fillEl, { opacity: 1, duration: 0.6, ease: "remotion.smooth" }, at + dur * 0.4);
      }
    },

    /**
     * 圆环/甜甜圈进度 — SVG <circle> stroke-dashoffset + 中心标签
     * circleEl: SVG circle 元素（需有 r 属性）
     * labelEl:  中心数字 DOM（可选）
     * opts: duration, ease
     */
    donutProgress: function (circleEl, labelEl, targetPct, tl, at, opts) {
      opts = opts || {};
      var dur = opts.duration || 1.0;
      var ease = opts.ease || "remotion.snappy";
      var r = parseFloat(circleEl.getAttribute("r") ||
        (circleEl.r && circleEl.r.baseVal && circleEl.r.baseVal.value) || 45);
      var circ = 2 * Math.PI * r;
      var targetOffset = circ * (1 - targetPct / 100);
      gsap.set(circleEl, {
        strokeDasharray: circ, strokeDashoffset: circ,
        transformOrigin: "center", rotation: -90
      });
      tl.to(circleEl, { strokeDashoffset: targetOffset, duration: dur, ease: ease }, at);
      if (labelEl) {
        var obj = { val: 0 };
        tl.to(obj, {
          val: targetPct, duration: dur, ease: ease,
          onUpdate: function () { labelEl.textContent = Math.round(obj.val) + "%"; }
        }, at);
      }
    },

    /**
     * 气泡图 — 圆形元素从 scale:0 弹出
     * opts: stagger, ease
     */
    bubbleChart: function (selector, tl, at, opts) {
      opts = opts || {};
      var stagger = opts.stagger !== undefined ? opts.stagger : 0.1;
      gsap.utils.toArray(selector).forEach(function (el, i) {
        tl.fromTo(el,
          { scale: 0, opacity: 0 },
          { scale: 1, opacity: 0.88, duration: 0.55, ease: "remotion.spring" },
          at + i * stagger);
      });
    },

    /**
     * 热力格子 — 网格单元格逐个淡入（GitHub 贡献图风格）
     * opts: stagger（建议 0.02）
     */
    heatGrid: function (selector, tl, at, opts) {
      opts = opts || {};
      var stagger = opts.stagger !== undefined ? opts.stagger : 0.025;
      gsap.utils.toArray(selector).forEach(function (el, i) {
        tl.fromTo(el,
          { opacity: 0, scale: 0.4 },
          { opacity: 1, scale: 1, duration: 0.25, ease: "remotion.spring" },
          at + i * stagger);
      });
    },

    /**
     * 翻牌数字 — CSS rotateX 翻转模拟时钟牌
     * 最多 20 次视觉翻转（大范围自动采样）
     */
    flipCounter: function (el, from, to, duration, tl, at) {
      el.style.display = "inline-block";
      el.style.perspective = "200px";
      el.textContent = from;
      var total = Math.abs(to - from);
      var dir = to > from ? 1 : -1;
      var steps = Math.min(total, 20);
      var stepDur = duration / Math.max(steps, 1);
      for (var s = 0; s < steps; s++) {
        (function (si) {
          var t = at + si * stepDur;
          var nextVal = from + dir * Math.round((si + 1) * total / steps);
          tl.to(el, {
            rotateX: -90, duration: stepDur * 0.4, ease: "remotion.easeIn",
            onComplete: (function (v) {
              return function () { el.textContent = v; gsap.set(el, { rotateX: 90 }); };
            })(nextVal)
          }, t);
          tl.to(el, { rotateX: 0, duration: stepDur * 0.5, ease: "remotion.spring" }, t + stepDur * 0.4);
        })(s);
      }
    },

    /**
     * 人形图（Isotype）— 图标逐个弹出，前 N 个高亮其余变暗
     * opts: stagger, dim（未高亮 opacity，默认 0.2）
     */
    isotype: function (selector, highlightCount, tl, at, opts) {
      opts = opts || {};
      var stagger = opts.stagger !== undefined ? opts.stagger : 0.06;
      var dim = opts.dim !== undefined ? opts.dim : 0.2;
      gsap.utils.toArray(selector).forEach(function (el, i) {
        tl.fromTo(el,
          { scale: 0, opacity: 0 },
          { scale: 1, opacity: i < highlightCount ? 1 : dim, duration: 0.3, ease: "remotion.spring" },
          at + i * stagger);
      });
    },

    /* ══════════════════════════════════════════════════════════
     * 文字动效
     * ══════════════════════════════════════════════════════════ */

    /**
     * 批量交错入场（通用）
     * opts: from, to, ease, stagger
     */
    staggerIn: function (selector, tl, at, opts) {
      opts = opts || {};
      var from = opts.from || { opacity: 0, y: 28, scale: 0.94 };
      var to = opts.to || { opacity: 1, y: 0, scale: 1, duration: 0.55, ease: "remotion.snappy" };
      var stagger = opts.stagger !== undefined ? opts.stagger : 0.1;
      gsap.utils.toArray(selector).forEach(function (el, i) {
        tl.fromTo(el, from, Object.assign({}, to), at + i * stagger);
      });
    },

    /**
     * 逐字揭示（含金句关键词高亮）
     * opts: stagger, accentWords（命中词变金色）, accentColor
     */
    charReveal: function (el, tl, at, opts) {
      opts = opts || {};
      var stagger = opts.stagger || 0.04;
      var accentColor = opts.accentColor || "#d9a441";
      var accentWords = opts.accentWords || [];
      var text = el.textContent || el.innerText || "";
      var accentSet = {};
      if (accentWords.length) {
        accentWords.forEach(function (w) {
          var pos = text.indexOf(w);
          while (pos !== -1) {
            for (var j = 0; j < w.length; j++) accentSet[pos + j] = true;
            pos = text.indexOf(w, pos + 1);
          }
        });
      }
      var html = "";
      for (var i = 0; i < text.length; i++) {
        var ch = text[i];
        var colorAttr = accentSet[i] ? ' style="color:' + accentColor + '"' : "";
        html += '<span class="cr-c"' + colorAttr + ">" + (ch === " " ? "&nbsp;" : ch) + "</span>";
      }
      el.innerHTML = html;
      el.querySelectorAll(".cr-c").forEach(function (span, i) {
        tl.fromTo(span,
          { opacity: 0, y: 36 },
          { opacity: 1, y: 0, duration: 0.45, ease: "remotion.snappy" },
          at + i * stagger);
      });
    },

    /**
     * 词组揭示 — 空格分词，整词入场（比逐字快，适合长句）
     * opts: stagger, ease
     */
    wordReveal: function (el, tl, at, opts) {
      opts = opts || {};
      var stagger = opts.stagger !== undefined ? opts.stagger : 0.08;
      var ease = opts.ease || "remotion.snappy";
      var text = el.textContent || el.innerText || "";
      el.innerHTML = text.trim().split(/\s+/).map(function (w) {
        return '<span class="wr-w">' + w + "</span>";
      }).join(" ");
      el.querySelectorAll(".wr-w").forEach(function (span, i) {
        tl.fromTo(span,
          { opacity: 0, y: 24 },
          { opacity: 1, y: 0, duration: 0.45, ease: ease },
          at + i * stagger);
      });
    },

    /**
     * 打字机 + 光标
     * opts: speed（每字秒数，默认 0.04）, cursor（显示光标，默认 true）, cursorChar
     */
    typewriter: function (el, text, tl, at, opts) {
      opts = opts || {};
      var speed = opts.speed !== undefined ? opts.speed : 0.04;
      var showCursor = opts.cursor !== false;
      var cursorChar = opts.cursorChar || "|";
      el.innerHTML = showCursor
        ? '<span class="tw-txt"></span><span class="tw-cur" style="animation:auBlink 0.7s step-end infinite;margin-left:1px">' + cursorChar + "</span>"
        : "";
      var textEl = showCursor ? el.querySelector(".tw-txt") : el;
      var obj = { n: 0 };
      tl.to(obj, {
        n: text.length, duration: text.length * speed, ease: "none",
        onUpdate: function () { textEl.textContent = text.slice(0, Math.round(obj.n)); },
        onComplete: function () { textEl.textContent = text; }
      }, at);
    },

    /**
     * 高亮扫线 — 半透明色块从左划过文字背景
     * opts: color, duration
     */
    highlightSweep: function (el, tl, at, opts) {
      opts = opts || {};
      var color = opts.color || "rgba(217,164,65,0.3)";
      var dur = opts.duration || 0.5;
      var hl = document.createElement("span");
      hl.style.cssText = "position:absolute;top:0;left:0;height:100%;width:0%;background:" +
        color + ";z-index:-1;pointer-events:none";
      el.style.position = "relative";
      el.insertBefore(hl, el.firstChild);
      tl.to(hl, { width: "100%", duration: dur, ease: "remotion.smooth" }, at);
    },

    /**
     * 文字溶解变形 — blur 渐隐再渐显切换词语
     * texts: 词语数组；interval: 每个词显示的秒数
     */
    morphText: function (el, texts, interval, tl, at) {
      el.textContent = texts[0];
      gsap.set(el, { opacity: 1, filter: "blur(0px)" });
      for (var i = 1; i < texts.length; i++) {
        (function (idx) {
          var t = at + idx * interval;
          tl.to(el, {
            opacity: 0, filter: "blur(10px)", duration: 0.3, ease: "remotion.easeIn",
            onComplete: function () { el.textContent = texts[idx]; }
          }, t - 0.3);
          tl.to(el, { opacity: 1, filter: "blur(0px)", duration: 0.4, ease: "remotion.snappy" }, t);
        })(i);
      }
    },

    /**
     * 行文字从左推入 — 每行 x:-60→0
     * opts: stagger, ease
     */
    lineSlideIn: function (selector, tl, at, opts) {
      opts = opts || {};
      var stagger = opts.stagger !== undefined ? opts.stagger : 0.12;
      var ease = opts.ease || "remotion.snappy";
      gsap.utils.toArray(selector).forEach(function (el, i) {
        tl.fromTo(el,
          { x: -60, opacity: 0 },
          { x: 0, opacity: 1, duration: 0.5, ease: ease },
          at + i * stagger);
      });
    },

    /* ══════════════════════════════════════════════════════════
     * UI 组件
     * ══════════════════════════════════════════════════════════ */

    /**
     * 卡片弹出（spring 过冲）
     * opts: stagger, scaleFrom, yFrom, ease
     */
    cardSpring: function (selector, tl, at, opts) {
      opts = opts || {};
      var stagger = opts.stagger !== undefined ? opts.stagger : 0.3;
      var scaleFrom = opts.scaleFrom !== undefined ? opts.scaleFrom : 0.82;
      var yFrom = opts.yFrom !== undefined ? opts.yFrom : 40;
      var ease = opts.ease || "remotion.spring";
      gsap.utils.toArray(selector).forEach(function (el, i) {
        tl.fromTo(el,
          { scale: scaleFrom, y: yFrom, opacity: 0 },
          { scale: 1, y: 0, opacity: 1, duration: 0.55, ease: ease },
          at + i * stagger);
      });
    },

    /**
     * 进度条填充 — 宽度从 0 → targetPct%
     * opts: duration, ease
     */
    progressBar: function (fillEl, targetPct, tl, at, opts) {
      opts = opts || {};
      gsap.set(fillEl, { width: "0%" });
      tl.to(fillEl, {
        width: targetPct + "%",
        duration: opts.duration || 0.8,
        ease: opts.ease || "remotion.snappy"
      }, at);
    },

    /**
     * 圆形进度环 — SVG circle stroke-dashoffset + 中心百分比
     * opts: duration, ease
     */
    progressRing: function (circleEl, labelEl, targetPct, tl, at, opts) {
      opts = opts || {};
      var dur = opts.duration || 1.0;
      var ease = opts.ease || "remotion.snappy";
      var r = parseFloat(circleEl.getAttribute("r") || 45);
      var circ = 2 * Math.PI * r;
      gsap.set(circleEl, {
        strokeDasharray: circ, strokeDashoffset: circ,
        transformOrigin: "center", rotation: -90
      });
      tl.to(circleEl, { strokeDashoffset: circ * (1 - targetPct / 100), duration: dur, ease: ease }, at);
      if (labelEl) {
        var obj = { val: 0 };
        tl.to(obj, {
          val: targetPct, duration: dur, ease: ease,
          onUpdate: function () { labelEl.textContent = Math.round(obj.val) + "%"; }
        }, at);
      }
    },

    /**
     * 时间轴节点 — 竖线生长 + 节点逐个弹出 + 标签入场
     * opts: stagger, lineDuration
     */
    timelineNodes: function (lineEl, dotsSelector, labelsSelector, tl, at, opts) {
      opts = opts || {};
      var dots = gsap.utils.toArray(dotsSelector);
      var labels = labelsSelector ? gsap.utils.toArray(labelsSelector) : [];
      var stagger = opts.stagger !== undefined ? opts.stagger : 0.35;
      var lineDur = opts.lineDuration || (dots.length * stagger * 0.85);
      if (lineEl) {
        tl.fromTo(lineEl,
          { scaleY: 0, transformOrigin: "top center" },
          { scaleY: 1, duration: lineDur, ease: "remotion.smooth" },
          at);
      }
      dots.forEach(function (dot, i) {
        tl.fromTo(dot,
          { scale: 0, opacity: 0 },
          { scale: 1, opacity: 1, duration: 0.35, ease: "remotion.spring" },
          at + i * stagger);
        if (labels[i]) {
          tl.fromTo(labels[i],
            { x: 20, opacity: 0 },
            { x: 0, opacity: 1, duration: 0.4, ease: "remotion.snappy" },
            at + i * stagger + 0.1);
        }
      });
    },

    /**
     * 标签/Tag 弹出 — 圆角标签 scale 弹入
     * opts: stagger, ease
     */
    tagPop: function (selector, tl, at, opts) {
      opts = opts || {};
      var stagger = opts.stagger !== undefined ? opts.stagger : 0.1;
      gsap.utils.toArray(selector).forEach(function (el, i) {
        tl.fromTo(el,
          { scale: 0.6, opacity: 0 },
          { scale: 1, opacity: 1, duration: 0.4, ease: opts.ease || "remotion.spring" },
          at + i * stagger);
      });
    },

    /**
     * 对话气泡 — 左右交替入场
     * data-side="left|right" 控制方向（默认奇偶交替）
     * opts: stagger, ease
     */
    chatBubbles: function (selector, tl, at, opts) {
      opts = opts || {};
      var stagger = opts.stagger !== undefined ? opts.stagger : 0.55;
      var ease = opts.ease || "remotion.spring";
      gsap.utils.toArray(selector).forEach(function (el, i) {
        var side = el.dataset.side || (i % 2 === 0 ? "left" : "right");
        tl.fromTo(el,
          { x: side === "right" ? 50 : -50, opacity: 0, scale: 0.9 },
          { x: 0, opacity: 1, scale: 1, duration: 0.45, ease: ease },
          at + i * stagger);
      });
    },

    /* ══════════════════════════════════════════════════════════
     * 氛围效果
     * ══════════════════════════════════════════════════════════ */

    /**
     * 涟漪脉冲 — 向外扩散圆环（containerEl 需 overflow:visible）
     * opts: cycles, color, size（像素数）
     */
    ripplePulse: function (containerEl, tl, at, opts) {
      opts = opts || {};
      var cycles = opts.cycles || 3;
      var color = opts.color || "#d9a441";
      var size = opts.size || 60;
      containerEl.style.position = "relative";
      containerEl.style.overflow = "visible";
      for (var i = 0; i < cycles; i++) {
        (function (idx) {
          var ring = document.createElement("div");
          ring.style.cssText = "position:absolute;border-radius:50%;border:2px solid " + color +
            ";top:50%;left:50%;width:" + size + "px;height:" + size + "px;" +
            "margin-top:-" + (size / 2) + "px;margin-left:-" + (size / 2) + "px;" +
            "opacity:0;pointer-events:none;box-sizing:border-box";
          containerEl.appendChild(ring);
          tl.fromTo(ring,
            { scale: 1, opacity: 0.7 },
            { scale: 2.5, opacity: 0, duration: 1.0, ease: "remotion.easeIn" },
            at + idx * 0.4);
        })(i);
      }
    },

    /**
     * SVG 路径描绘 — stroke-dashoffset 从头到尾描出路径
     * opts: duration, ease
     */
    pathDraw: function (pathEl, tl, at, opts) {
      opts = opts || {};
      var len = (pathEl.getTotalLength && pathEl.getTotalLength()) || 300;
      gsap.set(pathEl, { strokeDasharray: len, strokeDashoffset: len });
      tl.to(pathEl, {
        strokeDashoffset: 0,
        duration: opts.duration || 0.8,
        ease: opts.ease || "remotion.smooth"
      }, at);
    },

    /**
     * 颜色插值过渡 — GSAP 直接动画 CSS 颜色属性
     * opts: duration, ease, prop（默认 "color"）
     */
    colorMorph: function (el, toColor, tl, at, opts) {
      opts = opts || {};
      var prop = opts.prop || "color";
      var tweenProps = { duration: opts.duration || 0.8, ease: opts.ease || "remotion.smooth" };
      tweenProps[prop] = toColor;
      tl.to(el, tweenProps, at);
    },

    /**
     * 扫光 — 斜向高光条从左划过元素
     * opts: duration
     */
    shimmer: function (el, tl, at, opts) {
      opts = opts || {};
      var dur = opts.duration || 0.7;
      var ov = document.createElement("div");
      ov.style.cssText = "position:absolute;top:0;left:-80%;width:60%;height:100%;" +
        "background:linear-gradient(105deg,transparent 35%,rgba(255,255,255,0.18) 50%,transparent 65%);" +
        "pointer-events:none;z-index:10";
      el.style.overflow = "hidden";
      el.style.position = "relative";
      el.appendChild(ov);
      tl.to(ov, { left: "130%", duration: dur, ease: "none" }, at);
    },

    /**
     * 粒子爆出 — 元素出现时向外散射小圆点
     * opts: count, color, distance
     */
    particleBurst: function (el, tl, at, opts) {
      opts = opts || {};
      var count = opts.count || 8;
      var color = opts.color || "#d9a441";
      var dist = opts.distance || 55;
      el.style.position = "relative";
      el.style.overflow = "visible";
      for (var i = 0; i < count; i++) {
        (function (idx) {
          var dot = document.createElement("div");
          var angle = (idx / count) * 2 * Math.PI;
          dot.style.cssText = "position:absolute;width:5px;height:5px;border-radius:50%;background:" +
            color + ";top:50%;left:50%;transform:translate(-50%,-50%);pointer-events:none;opacity:0";
          el.appendChild(dot);
          tl.fromTo(dot,
            { x: 0, y: 0, opacity: 1, scale: 1 },
            {
              x: Math.cos(angle) * dist, y: Math.sin(angle) * dist,
              opacity: 0, scale: 0.3, duration: 0.65, ease: "remotion.easeIn"
            }, at);
        })(i);
      }
    },

    /**
     * 3D 翻转卡 — CSS perspective rotateY
     * frontEl/backEl 放在同一 perspective 容器内
     * opts: duration, ease
     */
    cardFlip3D: function (frontEl, backEl, tl, at, opts) {
      opts = opts || {};
      var dur = opts.duration || 0.6;
      var ease = opts.ease || "remotion.smooth";
      var container = frontEl.parentElement;
      if (container) container.style.perspective = container.style.perspective || "800px";
      frontEl.style.backfaceVisibility = "hidden";
      if (backEl) backEl.style.backfaceVisibility = "hidden";
      gsap.set(backEl, { rotateY: 180 });
      tl.to(frontEl, { rotateY: -180, duration: dur, ease: ease }, at);
      if (backEl) tl.to(backEl, { rotateY: 0, duration: dur, ease: ease }, at);
    },

    /**
     * 背景渐变动态 — backgroundPosition 缓慢往返漂移
     * el 需已设置渐变 background，本函数只驱动 backgroundPosition
     * ⚠️ 使用两段顺序 tween 而非 repeat:-1（hf 禁止无限循环）
     * opts: duration（单程秒数，默认 3.0）
     */
    gradientFlow: function (el, tl, at, opts) {
      opts = opts || {};
      var dur = opts.duration || 3.0;
      gsap.set(el, { backgroundSize: "200% 200%", backgroundPosition: "0% 0%" });
      tl.to(el, { backgroundPosition: "100% 100%", duration: dur, ease: "remotion.smooth" }, at);
      tl.to(el, { backgroundPosition: "0% 0%", duration: dur, ease: "remotion.smooth" }, at + dur);
    }

  };

})();
