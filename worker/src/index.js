const URL_TEMPLATE = "https://postings.speechwire.com/r-uil-academics.php?";
const COMPETITIONS = {
  1: "Accounting",
  8: "Calculator",
  9: "CS",
  3: "Current Events",
  10: "Math",
  11: "Number Sense",
  12: "Science",
  7: "Spelling",
  4: "Lit Crit",
  6: "Social Studies",
};

function corsHeaders(origin = "*") {
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function jsonResponse(payload, status = 200, origin = "*", extraHeaders = {}) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...corsHeaders(origin),
      ...extraHeaders,
    },
  });
}

async function req({ yearOffset, dist = "", reg = "", state = "", comp = "", conf = "" }) {
  const inp = `${URL_TEMPLATE}groupingid=${comp}&Submit=View+Postings&region=${reg}&district=${dist}&state=${state}&conference=${conf}&seasonid=${yearOffset}`;
  const response = await fetch(inp, { cf: { cacheTtl: 0, cacheEverything: false } });
  return response.text();
}

function extractPrintableRows(scrape) {
  const regex = /<tr>\s*(?:<td class='ddprint centered'>[\s\S]*?<\/td>\s*)+<\/tr>/g;
  const rows = [];
  let m;
  while ((m = regex.exec(scrape)) !== null) {
    rows.push(m[0]);
  }
  return rows;
}

function parseIndividualRows(scrape, token) {
  const printableRows = extractPrintableRows(scrape);
  let rows = printableRows.filter((row) => row.includes(token));
  if (rows.length === 0) {
    rows = printableRows.filter((row) => row.includes("HS"));
  }
  return rows;
}

function parseTeamRows(scrape) {
  return extractPrintableRows(scrape).filter((row) => (row.match(/<br>/g) || []).length >= 2);
}

function toNumber(value) {
  const n = Number(value);
  return Number.isInteger(n) ? n : Number.parseFloat(value);
}

async function processSingleDistrict({ districtNum, subj, compName, conf, yearOffset }) {
  try {
    const scrape = await req({ yearOffset, dist: String(districtNum), comp: String(subj), conf });
    const tmp = `${districtNum < 10 ? "0" : ""}${districtNum}`;
    let indivPlaces = parseIndividualRows(scrape, `${tmp}-${conf}A`);

    const indivResults = [];
    const teamResults = [];
    const mxbio = {};
    const mxchem = {};
    const mxphys = {};

    if (indivPlaces.length === 0) {
      return { emptyDistricts: [districtNum] };
    }

    for (const row of indivPlaces) {
      const values = [...row.matchAll(/<td class='ddprint centered'>(.*?)<\/td>/g)].map((x) => x[1]);
      const place = values[0];
      const school = values[1];
      const name = values[2]?.trim();
      const score = toNumber(values[subj % 10 === 1 ? values.length - 3 : values.length - 4]);
      let tup = [score, place, name, school, `District ${districtNum}`];

      if (subj === 12) {
        const bio = Number.parseInt(values[4], 10);
        const chem = Number.parseInt(values[5], 10);
        const phys = Number.parseInt(values[6], 10);
        tup = [score, place, name, school, `District ${districtNum}`, bio, chem, phys];
        mxbio[districtNum] = Math.max(mxbio[districtNum] ?? bio, bio);
        mxchem[districtNum] = Math.max(mxchem[districtNum] ?? chem, chem);
        mxphys[districtNum] = Math.max(mxphys[districtNum] ?? phys, phys);
      }
      indivResults.push(tup);
    }

    const teamPlaces = parseTeamRows(scrape);
    for (let idx = 0; idx < teamPlaces.length; idx += 1) {
      const x = teamPlaces[idx].replaceAll("\u00a0", " ");
      if ((x.match(/<br>/g) || []).length < 2) continue;
      try {
        const place = x.match(/<td class='ddprint centered'>(.*?)<\/td>/)?.[1]?.trim();
        const schoolMatch = x.match(/<td class='ddprint centered'>(.*?)<span/s)?.[1]?.trim() || "";
        const school = schoolMatch.includes(">") ? schoolMatch.slice(schoolMatch.lastIndexOf(">") + 1).trim() : schoolMatch;
        const numbers = [...x.matchAll(/<td class='ddprint centered'>(-?\d+)<\/td>/g)].map((m) => m[1]);
        let score = 0;
        let progScore = -999;
        if (compName === "CS") {
          progScore = numbers[0] ?? -999;
          score = numbers[1] ?? 0;
        } else {
          score = numbers[0] ?? 0;
        }
        const names = x
          .split("<br>")
          .slice(1)
          .map((n) => (n.includes("<") ? n.slice(0, n.indexOf("<")) : n).trim())
          .filter(Boolean);
        if (!names.length) continue;
        const teamScores = indivResults
          .filter((tup) => names.includes(tup[2]))
          .sort((a, b) => b[0] - a[0]);
        teamResults.push([
          Number.parseInt(score, 10),
          compName === "CS" ? Number.parseInt(progScore, 10) : -999,
          teamScores.length <= 3 ? -999 : teamScores[3][0],
          place,
          school,
          `District ${districtNum}`,
          names,
        ]);
      } catch (_) {
        continue;
      }
    }

    return { indivResults, teamResults, mxbio, mxchem, mxphys, emptyDistricts: [] };
  } catch (_) {
    return { emptyDistricts: [districtNum] };
  }
}

async function districtParser({ regNumber, subj, compName, conf, yearOffset }) {
  const districtNums = [];
  for (let i = regNumber * 8 - 7; i <= regNumber * 8; i += 1) districtNums.push(i);
  const districtResults = await Promise.all(
    districtNums.map((districtNum) => processSingleDistrict({ districtNum, subj, compName, conf, yearOffset })),
  );

  const indivResults = [];
  const teamResults = [];
  const mxbio = {};
  const mxchem = {};
  const mxphys = {};
  const emptyDistricts = [];

  for (const result of districtResults) {
    if (!result.indivResults) {
      emptyDistricts.push(...result.emptyDistricts);
      continue;
    }
    indivResults.push(...result.indivResults);
    teamResults.push(...result.teamResults);
    if (subj === 12) {
      for (const [k, v] of Object.entries(result.mxbio)) mxbio[k] = Math.max(mxbio[k] ?? v, v);
      for (const [k, v] of Object.entries(result.mxchem)) mxchem[k] = Math.max(mxchem[k] ?? v, v);
      for (const [k, v] of Object.entries(result.mxphys)) mxphys[k] = Math.max(mxphys[k] ?? v, v);
    }
  }

  indivResults.sort((a, b) => (b[0] - a[0]));
  teamResults.sort((a, b) => ((b[0] - a[0]) || (b[1] - a[1]) || (b[2] - a[2])));
  const allIndiv = [...indivResults];
  const allTeam = [...teamResults];

  const filteredTeams = [];
  let found = false;
  for (const x of teamResults) {
    if (x[3] === "1st") filteredTeams.push(x);
    else if (x[3] === "2nd" && !found) {
      filteredTeams.push(x);
      found = true;
    }
  }

  const filteredIndiv = [];
  for (const x of indivResults) {
    let foundOnTeam = filteredTeams.some((team) => team[6].includes(x[2]));
    if (subj === 12) {
      const district = Number.parseInt(String(x[4]).slice(9), 10);
      const b = mxbio[district] === x[x.length - 3];
      const c = mxchem[district] === x[x.length - 2];
      const p = mxphys[district] === x[x.length - 1];
      foundOnTeam = foundOnTeam || b || c || p;
    }
    if (["1st", "2nd", "3rd"].includes(x[1]) || foundOnTeam) filteredIndiv.push(x);
  }

  return { indivResults: filteredIndiv, teamResults: filteredTeams, allIndiv, allTeam, emptyDistricts };
}

async function regionalParser({ subj, compName, conf, yearOffset }) {
  const indivResults = [];
  const teamResults = [];
  const mxbio = {};
  const mxchem = {};
  const mxphys = {};

  for (let i = 1; i <= 4; i += 1) {
    try {
      const scrape = await req({ yearOffset, reg: String(i), comp: String(subj), conf });
      let indivPlaces = parseIndividualRows(scrape, `${conf}A`);
      if (indivPlaces.length === 0) continue;

      for (const row of indivPlaces) {
        const values = [...row.matchAll(/<td class='ddprint centered'>(.*?)<\/td>/g)].map((x) => x[1]);
        const place = values[0];
        const school = values[1];
        const name = values[2]?.trim();
        const score = toNumber(values[subj % 10 === 1 ? values.length - 3 : values.length - 4]);
        let tup = [score, place, name, school, `Region ${i}`];
        if (subj === 12) {
          const bio = Number.parseInt(values[4], 10);
          const chem = Number.parseInt(values[5], 10);
          const phys = Number.parseInt(values[6], 10);
          tup = [score, place, name, school, `Region ${i}`, bio, chem, phys];
          mxbio[i] = Math.max(mxbio[i] ?? bio, bio);
          mxchem[i] = Math.max(mxchem[i] ?? chem, chem);
          mxphys[i] = Math.max(mxphys[i] ?? phys, phys);
        }
        indivResults.push(tup);
      }

      const teamPlaces = parseTeamRows(scrape);
      for (let idx = 0; idx < teamPlaces.length; idx += 1) {
        const x = teamPlaces[idx].replaceAll("\u00a0", " ");
        if ((x.match(/<br>/g) || []).length < 2) continue;
        try {
          const place = x.match(/<td class='ddprint centered'>(.*?)<\/td>/)?.[1]?.trim();
          const schoolMatch = x.match(/<td class='ddprint centered'>(.*?)<span/s)?.[1]?.trim() || "";
          const school = schoolMatch.includes(">") ? schoolMatch.slice(schoolMatch.lastIndexOf(">") + 1).trim() : schoolMatch;
          const numbers = [...x.matchAll(/<td class='ddprint centered'>(-?\d+)<\/td>/g)].map((m) => m[1]);
          let score = 0;
          let progScore = -999;
          if (compName === "CS") {
            progScore = numbers[0] ?? -999;
            score = numbers[1] ?? 0;
          } else {
            score = numbers[0] ?? 0;
          }
          const names = x
            .split("<br>")
            .slice(1)
            .map((n) => (n.includes("<") ? n.slice(0, n.indexOf("<")) : n).trim())
            .filter(Boolean);
          if (!names.length) continue;
          const teamScores = indivResults.filter((tup) => names.includes(tup[2])).sort((a, b) => b[0] - a[0]);
          teamResults.push([
            Number.parseInt(score, 10),
            compName === "CS" ? Number.parseInt(progScore, 10) : -999,
            teamScores.length <= 3 ? -999 : teamScores[3][0],
            place,
            school,
            `Region ${i}`,
            names,
          ]);
        } catch (_) {
          continue;
        }
      }
    } catch (_) {
      continue;
    }
  }

  indivResults.sort((a, b) => (b[0] - a[0]));
  teamResults.sort((a, b) => ((b[0] - a[0]) || (b[1] - a[1]) || (b[2] - a[2])));
  const allIndiv = [...indivResults];
  const allTeam = [...teamResults];

  const filteredTeams = [];
  let found = false;
  for (const x of teamResults) {
    if (x[3] === "1st") filteredTeams.push(x);
    else if (x[3] === "2nd" && !found) {
      filteredTeams.push(x);
      found = true;
    }
  }

  const filteredIndiv = [];
  for (const x of indivResults) {
    let foundOnTeam = filteredTeams.some((team) => team[6].includes(x[2]));
    if (subj === 12) {
      const region = Number.parseInt(String(x[4]).slice(7), 10);
      const b = mxbio[region] === x[x.length - 3];
      const c = mxchem[region] === x[x.length - 2];
      const p = mxphys[region] === x[x.length - 1];
      foundOnTeam = foundOnTeam || b || c || p;
    }
    if (["1st", "2nd", "3rd"].includes(x[1]) || foundOnTeam) filteredIndiv.push(x);
  }

  return { indivResults: filteredIndiv, teamResults: filteredTeams, allIndiv, allTeam };
}

async function runForChoice({ choice, region, subj, compName, conf, yearOffset }) {
  if (choice === 1) return districtParser({ regNumber: Number.parseInt(region, 10), subj, compName, conf, yearOffset });
  if (choice === 2) {
    const indivResults = [];
    const teamResults = [];
    const allIndiv = [];
    const allTeam = [];
    const emptyDistricts = [];
    for (let r = 1; r <= 4; r += 1) {
      const x = await districtParser({ regNumber: r, subj, compName, conf, yearOffset });
      indivResults.push(...x.indivResults);
      teamResults.push(...x.teamResults);
      allIndiv.push(...x.allIndiv);
      allTeam.push(...x.allTeam);
      emptyDistricts.push(...x.emptyDistricts);
    }
    indivResults.sort((a, b) => (b[0] - a[0]));
    teamResults.sort((a, b) => ((b[0] - a[0]) || (b[1] - a[1]) || (b[2] - a[2])));
    allIndiv.sort((a, b) => (b[0] - a[0]));
    allTeam.sort((a, b) => ((b[0] - a[0]) || (b[1] - a[1]) || (b[2] - a[2])));
    return { indivResults, teamResults, allIndiv, allTeam, emptyDistricts };
  }
  const x = await regionalParser({ subj, compName, conf, yearOffset });
  return { ...x, emptyDistricts: [] };
}

async function buildResultsPayload({ year, confInput, subj, choice, region, selfOrigin, selfService }) {
  const compName = COMPETITIONS[subj];
  const yearOffset = year - 2008;
  const classificationMode = confInput === 0;

  let indivResults = [];
  let teamResults = [];
  let allIndiv = [];
  let allTeam = [];
  let emptyDistricts = [];

  if (classificationMode) {
    for (let c = 1; c <= 6; c += 1) {
      let x;
      if (choice === 2) {
        const internalUrl = new URL("/internal/district-all-regions", selfOrigin);
        const res = await selfService.fetch(internalUrl.toString(), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ year, conf: c, comp: subj }),
        });
        x = await res.json();
      } else {
        x = await runForChoice({ choice, region, subj, compName, conf: c, yearOffset });
      }
      const label = `${c}A`;
      indivResults.push(...x.indivResults.map((t) => [...t, label]));
      teamResults.push(...x.teamResults.map((t) => [...t, label]));
      allIndiv.push(...x.allIndiv.map((t) => [...t, label]));
      allTeam.push(...x.allTeam.map((t) => [...t, label]));
      emptyDistricts.push(...x.emptyDistricts.map((d) => `${label} district ${d}`));
    }
    indivResults.sort((a, b) => (b[0] - a[0]));
    teamResults.sort((a, b) => ((b[0] - a[0]) || (b[1] - a[1]) || (b[2] - a[2])));
    allIndiv.sort((a, b) => (b[0] - a[0]));
    allTeam.sort((a, b) => ((b[0] - a[0]) || (b[1] - a[1]) || (b[2] - a[2])));
  } else {
    const x = await runForChoice({ choice, region, subj, compName, conf: confInput, yearOffset });
    ({ indivResults, teamResults, allIndiv, allTeam, emptyDistricts } = x);
  }

  const formattedIndiv = [];
  const formattedAllIndiv = [];
  let currentRank = 1;
  let prevScore = null;

  const qualifiedIndivKeys = new Set(indivResults.map((q) => JSON.stringify(q)));

  for (let res of allIndiv) {
    let clsLabel = null;
    if (classificationMode) {
      clsLabel = res[res.length - 1];
      res = res.slice(0, -1);
    }
    const score = Number.parseInt(res[0], 10);
    if (score !== prevScore) currentRank = formattedAllIndiv.length + 1;
    prevScore = score;

    const isQualified = qualifiedIndivKeys.has(JSON.stringify(classificationMode ? [...res, clsLabel] : res));
    const result = subj === 12
      ? { rank: currentRank, score, name: res[2], school: res[3], district: res[4], bio: res[5], chem: res[6], phys: res[7], qualified: isQualified }
      : { rank: currentRank, score, name: res[2], school: res[3], district: res[4], qualified: isQualified };
    if (compName === "CS" && res.length > 5 && subj !== 12) result.prog_score = res[5];
    if (clsLabel) result.classification = clsLabel;
    formattedAllIndiv.push(result);
    if (isQualified) formattedIndiv.push({ ...result });
  }

  prevScore = null;
  currentRank = 1;
  for (const result of formattedIndiv) {
    const score = result.score;
    if (score !== prevScore) currentRank = formattedIndiv.filter((r) => r.score > score).length + 1;
    result.rank = currentRank;
    prevScore = score;
  }

  const formattedTeam = [];
  const formattedAllTeam = [];
  currentRank = 1;
  prevScore = null;

  const qualifiedTeamKeys = new Set(teamResults.map((q) => JSON.stringify(q)));

  for (let res of allTeam) {
    let clsLabel = null;
    if (classificationMode) {
      clsLabel = res[res.length - 1];
      res = res.slice(0, -1);
    }
    const score = res[0];
    if (score !== prevScore) currentRank = formattedAllTeam.length + 1;
    prevScore = score;
    const isQualified = qualifiedTeamKeys.has(JSON.stringify(classificationMode ? [...res, clsLabel] : res));
    const result = {
      rank: currentRank,
      score,
      school: res[4],
      district: res[5],
      names: res[6],
      qualified: isQualified,
      fourth: Number.parseInt(res[2], 10),
      prog_score: Number.parseInt(res[1], 10),
    };
    if (clsLabel) result.classification = clsLabel;
    formattedAllTeam.push(result);
    if (isQualified) formattedTeam.push({ ...result });
  }

  prevScore = null;
  currentRank = 1;
  for (const result of formattedTeam) {
    const cur = [result.score, result.prog_score, result.fourth];
    const prev = prevScore;
    if (!prev || prev[0] !== cur[0] || prev[1] !== cur[1] || prev[2] !== cur[2]) {
      currentRank = formattedTeam.filter((r) => {
        const t = [r.score, r.prog_score, r.fourth];
        return t[0] > cur[0] || (t[0] === cur[0] && (t[1] > cur[1] || (t[1] === cur[1] && t[2] > cur[2])));
      }).length + 1;
    }
    result.rank = currentRank;
    prevScore = cur;
  }

  return {
    individual: formattedIndiv,
    team: formattedTeam,
    all_individual: formattedAllIndiv,
    all_team: formattedAllTeam,
    empty_districts: emptyDistricts,
    classification_mode: classificationMode,
  };
}

export default {
  async fetch(request, env) {
    const origin = env.ALLOWED_ORIGIN || "*";
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/health") {
      return jsonResponse({ ok: true }, 200, origin);
    }
    if (request.method === "POST" && url.pathname === "/internal/district-all-regions") {
      let body;
      try {
        body = await request.json();
      } catch {
        return jsonResponse({ error: "Invalid JSON body" }, 400, origin);
      }
      const year = Number.parseInt(body.year, 10);
      const conf = Number.parseInt(body.conf, 10);
      const subj = Number.parseInt(body.comp, 10);
      if (!COMPETITIONS[subj]) return jsonResponse({ error: "Invalid competition" }, 400, origin);
      if (![2023, 2024, 2025, 2026].includes(year)) return jsonResponse({ error: "Invalid year" }, 400, origin);
      if (![1, 2, 3, 4, 5, 6].includes(conf)) return jsonResponse({ error: "Invalid classification" }, 400, origin);

      const compName = COMPETITIONS[subj];
      const yearOffset = year - 2008;
      const result = await runForChoice({ choice: 2, region: "1", subj, compName, conf, yearOffset });
      return jsonResponse(result, 200, origin);
    }
    if (request.method !== "POST" || url.pathname !== "/results") {
      return jsonResponse({ error: "Not found" }, 404, origin);
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return jsonResponse({ error: "Invalid JSON body" }, 400, origin);
    }

    const year = Number.parseInt(body.year, 10);
    const confInput = Number.parseInt(body.conf, 10);
    const subj = Number.parseInt(body.comp, 10);
    const choice = Number.parseInt(body.choice, 10);
    const region = String(body.region || "1");

    if (!COMPETITIONS[subj]) return jsonResponse({ error: "Invalid competition" }, 400, origin);
    if (![2023, 2024, 2025, 2026].includes(year)) return jsonResponse({ error: "Invalid year" }, 400, origin);
    if (![0, 1, 2, 3, 4, 5, 6].includes(confInput)) return jsonResponse({ error: "Invalid classification" }, 400, origin);
    if (![1, 2, 3].includes(choice)) return jsonResponse({ error: "Invalid choice" }, 400, origin);
    if (choice === 1 && !["1", "2", "3", "4"].includes(region)) return jsonResponse({ error: "Invalid region" }, 400, origin);

    const cache = caches.default;
    const cacheUrl = new URL(request.url);
    cacheUrl.pathname = "/results-cache";
    cacheUrl.search = new URLSearchParams({
      year: String(year),
      conf: String(confInput),
      comp: String(subj),
      choice: String(choice),
      region,
    }).toString();
    const cacheKey = new Request(cacheUrl.toString(), { method: "GET" });
    const cached = await cache.match(cacheKey);
    if (cached) return cached;

    try {
      const payload = await buildResultsPayload({ year, confInput, subj, choice, region, selfOrigin: url.origin, selfService: env.SELF });
      const response = jsonResponse(payload, 200, origin, { "Cache-Control": "public, max-age=120" });
      await cache.put(cacheKey, response.clone());
      return response;
    } catch (error) {
      return jsonResponse({ error: "Scrape failed", details: String(error?.message || error) }, 500, origin);
    }
  },
};
